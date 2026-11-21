use anyhow::Context;
use arc_swap::ArcSwapOption;
use chrono::{DateTime, Utc};
use once_cell::sync::Lazy;
use serde::de::DeserializeOwned;
use serde::{Deserialize, Serialize};
use sqlite_cache::{Cache, CacheConfig};
use std::future::Future;
use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

static CACHE: Lazy<ArcSwapOption<Cache>> = Lazy::new(|| {
    let cache = cache_file_name().and_then(|path| open_cache(&path));
    ArcSwapOption::new(match cache {
        Ok(cache) => Some(cache),
        Err(_) => {
            log::warn!("Cloud cache unavailable; continuing without a disk cache");
            sqlite_cache::rusqlite::Connection::open_in_memory()
                .ok()
                .and_then(|conn| Cache::new(CacheConfig::default(), conn).ok())
                .map(Arc::new)
        }
    })
});

fn cache_file_name() -> anyhow::Result<PathBuf> {
    let cache_dir = std::env::var("GOVEE_CACHE_DIR")
        .ok()
        .map(PathBuf::from)
        .or_else(dirs_next::cache_dir)
        .context("failed to resolve cache directory")?;

    Ok(cache_dir.join("govee2mqtt-cache.sqlite"))
}

fn open_cache(cache_file: &std::path::Path) -> anyhow::Result<Arc<Cache>> {
    let conn =
        sqlite_cache::rusqlite::Connection::open(cache_file).context("opening cloud cache")?;
    Ok(Arc::new(Cache::new(
        // We have low cardinality and can be pretty relaxed
        CacheConfig {
            flush_gc_ratio: 1024,
            flush_interval: Duration::from_secs(900),
            max_ttl: None,
        },
        conn,
    )?))
}

pub fn purge_cache() -> anyhow::Result<()> {
    let cache_file = cache_file_name()?;
    std::fs::remove_file(&cache_file)
        .with_context(|| format!("removing cache file {cache_file:?}"))?;
    CACHE.store(Some(open_cache(&cache_file)?));
    Ok(())
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
pub struct CacheGetOptions<'a> {
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

pub fn invalidate_key(topic: &str, key: &str) -> anyhow::Result<()> {
    if let Some(cache) = CACHE.load_full() {
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
    match CACHE.load_full() {
        Some(cache) => cache_get_from(&cache, options, future).await,
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
    let topic = cache.topic(options.topic)?;
    let (updater, current_value) = topic.get_for_update(options.key).await?;
    let now = Utc::now();

    let mut cache_entry: Option<CacheEntry<T>> = None;

    if let Some(current) = &current_value {
        match serde_json::from_slice::<CacheEntry<T>>(&current.data) {
            Ok(entry) => {
                if now < entry.expires {
                    log::trace!("cache hit for {}", options.key);
                    return entry.result.into_result();
                }

                cache_entry.replace(entry);
            }
            Err(err) => {
                log::warn!("Ignoring invalid cloud cache entry: {err:#}");
            }
        }
    }

    log::trace!("cache miss for {}", options.key);
    let value: anyhow::Result<CacheComputeResult<T>> = future.await;
    match value {
        Ok(CacheComputeResult::WithTtl(value, ttl)) => {
            let entry = CacheEntry {
                expires: Utc::now() + ttl,
                result: CacheResult::Ok(value.clone()),
            };

            let data = serde_json::to_string_pretty(&entry)?;
            updater.write(data.as_bytes(), options.hard_ttl)?;
            Ok(value)
        }
        Ok(CacheComputeResult::Value(value)) => {
            let entry = CacheEntry {
                expires: Utc::now() + options.soft_ttl,
                result: CacheResult::Ok(value.clone()),
            };

            let data = serde_json::to_string_pretty(&entry)?;
            updater.write(data.as_bytes(), options.hard_ttl)?;
            Ok(value)
        }
        Err(err) => match cache_entry.take() {
            Some(mut entry) if options.allow_stale => {
                entry.expires = Utc::now() + options.negative_ttl;

                log::warn!("Cloud cache refresh failed; using prior results");
                if matches!(&entry.result, CacheResult::Err(_)) {
                    entry.result = CacheResult::Err(format!("{err:#}"));
                }

                let data = serde_json::to_string_pretty(&entry)?;
                updater.write(data.as_bytes(), options.hard_ttl)?;

                entry.result.into_result()
            }
            _ => {
                let entry = CacheEntry {
                    expires: Utc::now() + options.negative_ttl,
                    result: CacheResult::Err(format!("{err:#}")),
                };

                let data = serde_json::to_string_pretty(&entry)?;
                updater.write(data.as_bytes(), options.hard_ttl)?;
                entry.result.into_result()
            }
        },
    }
}

#[cfg(test)]
mod sqlite_compatibility_tests {
    use super::*;

    #[tokio::test]
    async fn disk_cache_reopens_and_retries_expired_or_negative_entries() {
        let path =
            std::env::temp_dir().join(format!("govee-cache-{}.sqlite", uuid::Uuid::new_v4()));
        struct Cleanup(PathBuf);
        impl Drop for Cleanup {
            fn drop(&mut self) {
                let _ = std::fs::remove_file(&self.0);
            }
        }
        let _cleanup = Cleanup(path.clone());
        let options = CacheGetOptions {
            topic: "fixture",
            key: "device-list",
            soft_ttl: Duration::from_secs(60),
            hard_ttl: Duration::from_secs(60),
            negative_ttl: Duration::ZERO,
            allow_stale: false,
        };
        let cache = open_cache(&path).unwrap();
        let result = cache_get_from(&cache, options, async {
            Ok(CacheComputeResult::Value("fixture".to_string()))
        })
        .await
        .unwrap();
        assert_eq!(result, "fixture");
        drop(cache);

        let cache = open_cache(&path).unwrap();
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
        std::fs::write(&path, corrupt).unwrap();
        assert!(open_cache(&path).is_err());
        assert_eq!(std::fs::read(&path).unwrap(), corrupt);
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
