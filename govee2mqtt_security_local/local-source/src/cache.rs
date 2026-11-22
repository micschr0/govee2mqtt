use anyhow::Context;
use chrono::{DateTime, Utc};
use once_cell::sync::Lazy;
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sqlite_cache::rusqlite::{Connection, OpenFlags};
use sqlite_cache::{Cache, CacheConfig};
use std::future::Future;
use std::path::{Path, PathBuf};
use std::time::Duration;

static CACHE: Lazy<Option<Cache>> = Lazy::new(|| {
    let cache = cache_file_name().and_then(|path| open_cache(&path));
    match cache {
        Ok(cache) => Some(cache),
        Err(_) => {
            log::warn!("Cloud cache unavailable; continuing without a disk cache");
            memory_cache()
        }
    }
});

static AUTH_CACHE: Lazy<Option<Cache>> = Lazy::new(memory_cache);

fn memory_cache() -> Option<Cache> {
    Connection::open_in_memory()
        .ok()
        .and_then(|conn| Cache::new(CacheConfig::default(), conn).ok())
}

fn cache_file_name() -> anyhow::Result<PathBuf> {
    let cache_dir = std::env::var("GOVEE_CACHE_DIR")
        .ok()
        .map(PathBuf::from)
        .or_else(dirs_next::cache_dir)
        .context("failed to resolve cache directory")?;

    // The old database can contain unscoped credentials; never open or migrate it.
    Ok(cache_dir.join("govee2mqtt-cache-v2.sqlite"))
}

#[cfg(unix)]
fn prepare_cache_file(path: &Path) -> anyhow::Result<()> {
    use std::os::unix::fs::{OpenOptionsExt, PermissionsExt};

    match std::fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(path)
    {
        Ok(_) => {}
        Err(err) if err.kind() == std::io::ErrorKind::AlreadyExists => {}
        Err(err) => return Err(err.into()),
    }
    let metadata = std::fs::symlink_metadata(path)?;
    anyhow::ensure!(
        metadata.is_file() && metadata.permissions().mode() & 0o077 == 0,
        "Cloud cache file is not private"
    );
    Ok(())
}

fn open_cache(cache_file: &Path) -> anyhow::Result<Cache> {
    let flags = OpenFlags::SQLITE_OPEN_READ_WRITE
        | OpenFlags::SQLITE_OPEN_NO_MUTEX
        | OpenFlags::SQLITE_OPEN_NOFOLLOW;
    #[cfg(unix)]
    prepare_cache_file(cache_file)?;
    #[cfg(not(unix))]
    let flags = flags | OpenFlags::SQLITE_OPEN_CREATE;
    let conn = Connection::open_with_flags(cache_file, flags).context("opening cloud cache")?;
    Ok(Cache::new(
        // We have low cardinality and can be pretty relaxed
        CacheConfig {
            flush_gc_ratio: 1024,
            flush_interval: Duration::from_secs(900),
            max_ttl: None,
        },
        conn,
    )?)
}

pub fn purge_cache() -> anyhow::Result<()> {
    // Do not initialize caches on purge, especially on LAN-only installs.
    if let Some(Some(cache)) = Lazy::get(&AUTH_CACHE) {
        cache.clear().context("clearing auth cache")?;
    }
    if let Some(Some(cache)) = Lazy::get(&CACHE) {
        cache.clear().context("clearing cloud cache")?;
    }
    Ok(())
}

pub fn scoped_topic(api: &str, identity: &str) -> String {
    let mut digest = openssl::sha::Sha256::new();
    digest.update(api.as_bytes());
    digest.update(b"\0");
    digest.update(identity.as_bytes());
    format!("{api}:{}", data_encoding::HEXLOWER.encode(&digest.finish()))
}

#[derive(Deserialize, Serialize, Debug)]
struct CacheEntry<T> {
    expires: DateTime<Utc>,
    result: CacheResult<T>,
}

#[derive(Deserialize, Serialize, Debug)]
enum CacheResult<T> {
    Ok(T),
    Err(String),
}

impl<T> CacheResult<T> {
    fn into_result(self) -> anyhow::Result<T> {
        match self {
            Self::Ok(v) => Ok(v),
            Self::Err(err) => anyhow::bail!("{err}"),
        }
    }
}

#[derive(Copy, Clone, Debug)]
pub enum CacheStorage {
    Disk,
    MemoryOnly,
}

#[derive(Copy, Clone, Debug)]
pub struct CacheGetOptions<'a> {
    pub storage: CacheStorage,
    pub key: &'a str,
    pub topic: &'a str,
    pub soft_ttl: Duration,
    pub hard_ttl: Duration,
    pub negative_ttl: Duration,
    pub allow_stale: bool,
}

pub enum CacheComputeResult<T> {
    Value(T),
    WithTtl(T, Duration),
}

impl<T> CacheComputeResult<T> {
    #[allow(dead_code)]
    pub fn into_inner(self) -> T {
        match self {
            Self::Value(v) | Self::WithTtl(v, _) => v,
        }
    }
}

pub fn invalidate_auth_key(topic: &str, key: &str) -> anyhow::Result<()> {
    if let Some(cache) = AUTH_CACHE.as_ref() {
        cache.topic(topic)?.delete(key)?;
    }
    Ok(())
}

/// Cache an item with a soft TTL; we'll retry the operation
/// if the TTL has expired, but allow stale reads
pub async fn cache_get<T, Fut>(options: CacheGetOptions<'_>, future: Fut) -> anyhow::Result<T>
where
    T: Serialize + DeserializeOwned + std::fmt::Debug + Clone,
    Fut: Future<Output = anyhow::Result<CacheComputeResult<T>>>,
{
    let cache = match options.storage {
        CacheStorage::Disk => CACHE.as_ref(),
        CacheStorage::MemoryOnly => AUTH_CACHE.as_ref(),
    };
    match cache {
        Some(cache) => cache_get_from(cache, options, future).await,
        None => future.await.map(CacheComputeResult::into_inner),
    }
}

async fn cache_get_from<T, Fut>(
    cache: &Cache,
    options: CacheGetOptions<'_>,
    future: Fut,
) -> anyhow::Result<T>
where
    T: Serialize + DeserializeOwned + std::fmt::Debug + Clone,
    Fut: Future<Output = anyhow::Result<CacheComputeResult<T>>>,
{
    let Ok(topic) = cache.topic(options.topic) else {
        log::warn!("Could not open cloud cache topic; refreshing without cache");
        return future.await.map(CacheComputeResult::into_inner);
    };
    let Ok((updater, current_value)) = topic.get_for_update(options.key).await else {
        log::warn!("Could not read cloud cache entry; refreshing without cache");
        return future.await.map(CacheComputeResult::into_inner);
    };
    let now = Utc::now();

    let mut cache_entry: Option<CacheEntry<T>> = None;

    if let Some(current) = &current_value {
        match serde_json::from_slice::<CacheEntry<T>>(&current.data) {
            Ok(entry) => {
                if now < entry.expires {
                    return entry.result.into_result();
                }

                cache_entry.replace(entry);
            }
            Err(_) => {
                log::warn!("Ignoring invalid cloud cache entry");
            }
        }
    }

    let (ttl, result) = match future.await {
        Ok(CacheComputeResult::WithTtl(value, ttl)) => (ttl, Ok(value)),
        Ok(CacheComputeResult::Value(value)) => (options.soft_ttl, Ok(value)),
        Err(err) => match cache_entry.map(|entry| entry.result) {
            Some(CacheResult::Ok(value)) if options.allow_stale => {
                log::warn!("Cloud cache refresh failed; using prior results");
                (options.negative_ttl, Ok(value))
            }
            _ => (options.negative_ttl, Err(err)),
        },
    };
    let entry = CacheEntry {
        expires: Utc::now() + ttl,
        result: match &result {
            Ok(value) => CacheResult::Ok(value),
            // Only the in-process auth cache needs details for the 454 fallback.
            Err(err) => CacheResult::Err(match options.storage {
                CacheStorage::MemoryOnly => format!("{err:#}"),
                CacheStorage::Disk => "Cached cloud request failed".into(),
            }),
        },
    };
    let write = || -> anyhow::Result<()> {
        updater.write(&serde_json::to_vec(&entry)?, options.hard_ttl)?;
        Ok(())
    };
    if write().is_err() {
        log::warn!("Could not write cloud cache entry");
    }
    result
}

#[cfg(test)]
mod sqlite_compatibility_tests {
    use super::*;

    struct TestCachePath(PathBuf);

    impl TestCachePath {
        fn new() -> Self {
            Self(std::env::temp_dir().join(format!("govee-cache-{}.sqlite", uuid::Uuid::new_v4())))
        }
    }

    impl Drop for TestCachePath {
        fn drop(&mut self) {
            let _ = std::fs::remove_file(&self.0);
        }
    }

    const TEST_OPTIONS: CacheGetOptions<'static> = CacheGetOptions {
        storage: CacheStorage::Disk,
        topic: "fixture",
        key: "device-list",
        soft_ttl: Duration::from_secs(60),
        hard_ttl: Duration::from_secs(60),
        negative_ttl: Duration::ZERO,
        allow_stale: false,
    };

    #[test]
    fn purge_preserves_open_handles_and_skips_unused_disk_cache() {
        const CHILD: &str = "GOVEE_TEST_PURGE_CACHE_DIR";
        let ttl = TEST_OPTIONS.hard_ttl;
        if let Some(dir) = std::env::var_os(CHILD) {
            let dir = PathBuf::from(dir);
            let path = cache_file_name().unwrap();
            assert_eq!(path.parent(), Some(dir.as_path()));
            purge_cache().unwrap();
            assert!(!dir.exists());

            std::fs::create_dir(&dir).unwrap();
            let legacy = dir.join("govee2mqtt-cache.sqlite");
            std::fs::write(&legacy, b"legacy fixture").unwrap();
            purge_cache().unwrap();
            assert!(!path.exists());

            std::fs::write(&path, b"invalid database").unwrap();
            purge_cache().unwrap();
            assert_eq!(std::fs::read(&path).unwrap(), b"invalid database");
            std::fs::remove_file(&path).unwrap();

            let cache = CACHE.as_ref().unwrap();
            let first = cache.topic("inventory").unwrap();
            let second_cache = open_cache(&path).unwrap();
            let second = second_cache.topic("inventory").unwrap();
            let scenes = second_cache.topic("scenes").unwrap();
            let auth = AUTH_CACHE.as_ref().unwrap().topic("auth").unwrap();
            first.set("old", b"devices", ttl).unwrap();
            scenes.set("old", b"scenes", ttl).unwrap();
            auth.set("old", b"auth", ttl).unwrap();
            assert_eq!(second.get("old").unwrap().unwrap().data, b"devices");

            purge_cache().unwrap();
            assert!(first.get("old").unwrap().is_none());
            assert!(second.get("old").unwrap().is_none());
            assert!(scenes.get("old").unwrap().is_none());
            assert!(auth.get("old").unwrap().is_none());
            assert_eq!(std::fs::read(&legacy).unwrap(), b"legacy fixture");
            second.set("new", b"updated", ttl).unwrap();
            assert_eq!(first.get("new").unwrap().unwrap().data, b"updated");
            return;
        }

        // A separate test process keeps the cache path and lazy statics isolated.
        let path = TestCachePath::new();
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "cache::sqlite_compatibility_tests::purge_preserves_open_handles_and_skips_unused_disk_cache",
            ])
            .env(CHILD, &path.0)
            .env("GOVEE_CACHE_DIR", &path.0)
            .output()
            .unwrap();
        let reopened = if output.status.success() {
            open_cache(&path.0.join("govee2mqtt-cache-v2.sqlite")).and_then(|cache| {
                let topic = cache.topic("inventory")?;
                Ok((topic.get("old")?, topic.get("new")?))
            })
        } else {
            Err(anyhow::anyhow!(
                "isolated purge test failed: {}",
                String::from_utf8_lossy(&output.stdout)
            ))
        };
        if path.0.exists() {
            std::fs::remove_dir_all(&path.0).unwrap();
        }
        let (old, new) = reopened.unwrap();
        assert!(old.is_none());
        assert_eq!(new.unwrap().data, b"updated");
    }

    #[cfg(unix)]
    #[test]
    fn disk_cache_is_private_from_creation() {
        use std::os::unix::fs::PermissionsExt;

        let path = TestCachePath::new();
        let _cache = open_cache(&path.0).unwrap();
        assert_eq!(
            std::fs::metadata(&path.0).unwrap().permissions().mode() & 0o777,
            0o600
        );
    }

    #[cfg(unix)]
    #[test]
    fn nonprivate_cache_file_is_left_untouched() {
        use std::os::unix::fs::PermissionsExt;

        let path = TestCachePath::new();
        std::fs::write(&path.0, b"existing cache").unwrap();
        std::fs::set_permissions(&path.0, std::fs::Permissions::from_mode(0o644)).unwrap();
        assert_eq!(
            open_cache(&path.0).err().unwrap().to_string(),
            "Cloud cache file is not private"
        );
        assert_eq!(std::fs::read(&path.0).unwrap(), b"existing cache");
    }

    #[tokio::test]
    async fn disk_cache_does_not_persist_raw_errors() {
        let path = TestCachePath::new();
        let cache = open_cache(&path.0).unwrap();
        let options = CacheGetOptions {
            negative_ttl: Duration::from_secs(60),
            ..TEST_OPTIONS
        };
        let error = cache_get_from::<String, _>(&cache, options, async {
            anyhow::bail!("sensitive fixture response")
        })
        .await
        .unwrap_err();
        assert_eq!(error.to_string(), "sensitive fixture response");
        drop(cache);

        let cache = open_cache(&path.0).unwrap();
        let error =
            cache_get_from::<String, _>(&cache, options, async { panic!("negative cache miss") })
                .await
                .unwrap_err();
        assert_eq!(error.to_string(), "Cached cloud request failed");
    }

    #[tokio::test]
    async fn stale_data_is_reused_only_by_the_same_identity_after_reopen() {
        let path = TestCachePath::new();
        let cache = open_cache(&path.0).unwrap();
        let first = scoped_topic("http-api", "first fixture key");
        let options = CacheGetOptions {
            topic: &first,
            soft_ttl: Duration::ZERO,
            allow_stale: true,
            ..TEST_OPTIONS
        };
        let legacy = CacheGetOptions {
            topic: "http-api",
            ..options
        };
        cache_get_from(&cache, legacy, async {
            Ok(CacheComputeResult::Value("unscoped fixture".to_string()))
        })
        .await
        .unwrap();
        cache_get_from(&cache, options, async {
            Ok(CacheComputeResult::Value(
                "first fixture inventory".to_string(),
            ))
        })
        .await
        .unwrap();
        assert!(!first.contains("first fixture key"));
        drop(cache);

        let cache = open_cache(&path.0).unwrap();
        let same = scoped_topic("http-api", "first fixture key");
        let other = scoped_topic("http-api", "second fixture key");
        let wrong_api = scoped_topic("rest-api", "first fixture key");
        let unavailable = || async { anyhow::bail!("fixture API unavailable") };
        let stale = cache_get_from::<String, _>(
            &cache,
            CacheGetOptions {
                topic: &same,
                ..options
            },
            unavailable(),
        )
        .await
        .unwrap();
        assert_eq!(stale, "first fixture inventory");

        for topic in [&other, &wrong_api] {
            let error = cache_get_from::<String, _>(
                &cache,
                CacheGetOptions { topic, ..options },
                unavailable(),
            )
            .await
            .unwrap_err();
            assert_eq!(error.to_string(), "fixture API unavailable");
        }
    }

    #[tokio::test]
    async fn login_cache_keeps_454_in_memory_but_does_not_replay_prior_auth_after_restart() {
        let options = CacheGetOptions {
            key: "account-info",
            storage: CacheStorage::MemoryOnly,
            negative_ttl: Duration::from_secs(60),
            ..TEST_OPTIONS
        };
        let primary = scoped_topic("undoc-api", "first@example.invalid");
        let other = scoped_topic("undoc-api", "second@example.invalid");
        let options = CacheGetOptions {
            topic: &primary,
            ..options
        };
        let cache = memory_cache().unwrap();
        let _ = cache_get_from::<String, _>(&cache, options, async { anyhow::bail!("code 454") })
            .await
            .unwrap_err();
        let error = cache_get_from::<String, _>(&cache, options, async { panic!("cache miss") })
            .await
            .unwrap_err();
        assert_eq!(error.to_string(), "code 454");
        let other_options = CacheGetOptions {
            topic: &other,
            ..options
        };
        let value = cache_get_from(&cache, other_options, async {
            Ok(CacheComputeResult::Value("other account token".to_string()))
        })
        .await
        .unwrap();
        assert_eq!(value, "other account token");
        drop(cache);

        let cache = memory_cache().unwrap();
        let value = cache_get_from(&cache, other_options, async {
            Ok(CacheComputeResult::Value("refreshed token".to_string()))
        })
        .await
        .unwrap();
        assert_eq!(value, "refreshed token");
    }

    #[tokio::test]
    async fn disk_cache_reopens_and_retries_expired_or_negative_entries() {
        let path = TestCachePath::new();
        let options = TEST_OPTIONS;
        let cache = open_cache(&path.0).unwrap();
        let result = cache_get_from(&cache, options, async {
            Ok(CacheComputeResult::Value("fixture".to_string()))
        })
        .await
        .unwrap();
        assert_eq!(result, "fixture");
        drop(cache);

        let cache = open_cache(&path.0).unwrap();
        let result: String = cache_get_from(&cache, options, async { panic!("cache miss") })
            .await
            .unwrap();
        assert_eq!(result, "fixture");
        let expired = CacheGetOptions {
            soft_ttl: Duration::ZERO,
            key: "expired",
            ..options
        };
        cache_get_from(&cache, expired, async {
            Ok(CacheComputeResult::Value("old".to_string()))
        })
        .await
        .unwrap();
        let result = cache_get_from::<String, _>(&cache, expired, async {
            anyhow::bail!("fixture failure")
        })
        .await
        .unwrap_err();
        assert_eq!(result.to_string(), "fixture failure");
        let result = cache_get_from(&cache, expired, async {
            Ok(CacheComputeResult::Value("recovered".to_string()))
        })
        .await
        .unwrap();
        assert_eq!(result, "recovered");

        drop(cache);
        let corrupt = b"not a database";
        std::fs::write(&path.0, corrupt).unwrap();
        assert!(open_cache(&path.0).is_err());
        assert_eq!(std::fs::read(&path.0).unwrap(), corrupt);
    }

    #[test]
    fn cache_round_trip_with_bundled_sqlite() {
        let conn = sqlite_cache::rusqlite::Connection::open_in_memory().unwrap();
        let version: String = conn
            .query_row("select sqlite_version()", [], |row| row.get(0))
            .unwrap();
        let parts: Vec<u32> = version
            .split('.')
            .map(|part| part.parse().unwrap())
            .collect();
        assert!(
            parts.as_slice() >= [3, 54, 0].as_slice(),
            "SQLite {version} is vulnerable"
        );
        let cache = Cache::new(CacheConfig::default(), conn).unwrap();
        let topic = cache.topic("compatibility").unwrap();
        topic.set("key", b"value", Duration::from_secs(60)).unwrap();
        assert_eq!(topic.get("key").unwrap().unwrap().data, b"value");
        topic.delete("key").unwrap();
        assert!(topic.get("key").unwrap().is_none());
    }
}
