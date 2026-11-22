use crate::service::coordinator::Coordinator;
use crate::service::device::{Device, DeviceState};
use crate::service::state::StateHandle;
use anyhow::Context;
use axum::extract::{Path, Request, State};
use axum::http::{header, uri::Authority, HeaderValue, Method, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::Serialize;
use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr};
use tower_http::services::ServeDir;

const WEBUI_CSP: &str = "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'";

fn response_with_code<T: ToString + std::fmt::Display>(code: StatusCode, err: T) -> Response {
    if !code.is_success() {
        log::error!("err: {err:#}");
    }

    let mut response = Json(serde_json::json!({
        "code": code.as_u16(),
        "msg": format!("{err:#}")
    }))
    .into_response();
    *response.status_mut() = code;
    response
}

struct HttpError(Box<Response>);

impl IntoResponse for HttpError {
    fn into_response(self) -> Response {
        *self.0
    }
}

fn generic<T: ToString + std::fmt::Display>(err: T) -> HttpError {
    HttpError(Box::new(response_with_code(
        StatusCode::INTERNAL_SERVER_ERROR,
        err,
    )))
}

fn not_found<T: ToString + std::fmt::Display>(err: T) -> HttpError {
    HttpError(Box::new(response_with_code(StatusCode::NOT_FOUND, err)))
}

fn bad_request<T: ToString + std::fmt::Display>(err: T) -> HttpError {
    HttpError(Box::new(response_with_code(StatusCode::BAD_REQUEST, err)))
}

async fn resolve_device_for_control(
    state: &StateHandle,
    id: &str,
) -> Result<Coordinator, HttpError> {
    state
        .resolve_device_for_control(id)
        .await
        .map_err(not_found)
}

async fn resolve_device_read_only(state: &StateHandle, id: &str) -> Result<Device, HttpError> {
    state.resolve_device_read_only(id).await.map_err(not_found)
}

/// Returns a json array of device information
async fn list_devices(State(state): State<StateHandle>) -> Result<Response, HttpError> {
    let mut devices = state.devices().await;
    devices.sort_by_key(|d| (d.room_name().map(|name| name.to_string()), d.name()));

    #[derive(Serialize)]
    struct DeviceItem {
        pub sku: String,
        pub id: String,
        pub name: String,
        pub room: Option<String>,
        pub ip: Option<IpAddr>,
        pub state: Option<DeviceState>,
    }

    let devices: Vec<_> = devices
        .into_iter()
        .map(|d| DeviceItem {
            name: d.name(),
            room: d.room_name().map(|r| r.to_string()),
            ip: d.ip_addr(),
            state: d.device_state(),
            sku: d.sku,
            id: d.id,
        })
        .collect();

    Ok(Json(devices).into_response())
}

/// Turns on a given device
async fn device_power_on(
    State(state): State<StateHandle>,
    Path(id): Path<String>,
) -> Result<Response, HttpError> {
    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_power_on(&device, true)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Turns off a given device
async fn device_power_off(
    State(state): State<StateHandle>,
    Path(id): Path<String>,
) -> Result<Response, HttpError> {
    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_power_on(&device, false)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Sets the brightness level of a given device
async fn device_set_brightness(
    State(state): State<StateHandle>,
    Path((id, level)): Path<(String, u8)>,
) -> Result<Response, HttpError> {
    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_set_brightness(&device, level)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Sets the color temperature of a given device
async fn device_set_color_temperature(
    State(state): State<StateHandle>,
    Path((id, kelvin)): Path<(String, u32)>,
) -> Result<Response, HttpError> {
    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_set_color_temperature(&device, kelvin)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Sets the RGB color of a given device
async fn device_set_color(
    State(state): State<StateHandle>,
    Path((id, color)): Path<(String, String)>,
) -> Result<Response, HttpError> {
    let color = csscolorparser::parse(&color)
        .map_err(|err| bad_request(format!("error parsing color '{color}': {err}")))?;
    let [r, g, b, _a] = color.to_rgba8();

    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_set_color_rgb(&device, r, g, b)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Activates the named scene for a given device
async fn device_set_scene(
    State(state): State<StateHandle>,
    Path((id, scene)): Path<(String, String)>,
) -> Result<Response, HttpError> {
    let device = resolve_device_for_control(&state, &id).await?;

    state
        .device_set_scene(&device, &scene)
        .await
        .map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

/// Returns a JSON array of the available scene names for a given device
async fn device_list_scenes(
    State(state): State<StateHandle>,
    Path(id): Path<String>,
) -> Result<Response, HttpError> {
    let device = resolve_device_read_only(&state, &id).await?;

    Ok(Json(device.scene_names).into_response())
}

async fn list_one_clicks(State(state): State<StateHandle>) -> Result<Response, HttpError> {
    let undoc = state
        .get_undoc_client()
        .await
        .ok_or_else(|| anyhow::anyhow!("Undoc API client is not available"))
        .map_err(generic)?;
    let items = undoc.parse_one_clicks().await.map_err(generic)?;

    Ok(Json(items).into_response())
}

async fn activate_one_click(
    State(state): State<StateHandle>,
    Path(name): Path<String>,
) -> Result<Response, HttpError> {
    let undoc = state
        .get_undoc_client()
        .await
        .ok_or_else(|| anyhow::anyhow!("Undoc API client is not available"))
        .map_err(generic)?;
    let items = undoc.parse_one_clicks().await.map_err(generic)?;
    let item = items
        .iter()
        .find(|item| item.name == name)
        .ok_or_else(|| anyhow::anyhow!("didn't find item {name}"))
        .map_err(not_found)?;

    let iot = state
        .get_iot_client()
        .await
        .ok_or_else(|| anyhow::anyhow!("AWS IoT client is not available"))
        .map_err(generic)?;

    iot.activate_one_click(item).await.map_err(generic)?;

    Ok(response_with_code(StatusCode::OK, "ok"))
}

async fn redirect_to_index() -> Response {
    axum::response::Redirect::to("/assets/index.html").into_response()
}

fn direct_authority(value: &str) -> Option<Authority> {
    let authority: Authority = value.parse().ok()?;
    let host = authority.host();
    let suffix = value.strip_prefix(host)?;
    if !suffix.is_empty() {
        let port = suffix.strip_prefix(':')?;
        if !port.bytes().all(|byte| byte.is_ascii_digit()) || authority.port_u16().is_none() {
            return None;
        }
    }
    // DNS names are not trusted host identities for a direct IP listener.
    (host.eq_ignore_ascii_case("localhost")
        || host.parse::<Ipv4Addr>().is_ok()
        || host
            .strip_prefix('[')
            .and_then(|host| host.strip_suffix(']'))
            .is_some_and(|ip| ip.parse::<Ipv6Addr>().is_ok()))
    .then_some(authority)
}

fn same_authority(left: &Authority, right: &Authority) -> bool {
    left.host().eq_ignore_ascii_case(right.host())
        && left.port_u16().unwrap_or(80) == right.port_u16().unwrap_or(80)
}

async fn browser_policy(request: Request, next: Next) -> Response {
    let forbidden = || StatusCode::FORBIDDEN.into_response();
    let headers = request.headers();
    let mut hosts = headers.get_all(header::HOST).iter();
    let Some(host) = hosts
        .next()
        .and_then(|value| direct_authority(value.to_str().ok()?))
    else {
        return forbidden();
    };
    if hosts.next().is_some()
        || request
            .uri()
            .scheme_str()
            .is_some_and(|scheme| scheme != "http")
        || request.uri().authority().is_some_and(|target| {
            direct_authority(target.as_str()).is_none_or(|target| !same_authority(&host, &target))
        })
    {
        return forbidden();
    }

    let api = request.uri().path().starts_with("/api/");
    let valid_browser_context = if api {
        let read = matches!(*request.method(), Method::GET | Method::HEAD);
        let mut origins = headers.get_all(header::ORIGIN).iter();
        let valid_origin = origins.next().is_none_or(|value| {
            value
                .to_str()
                .ok()
                .and_then(|value| direct_authority(value.strip_prefix("http://")?))
                .is_some_and(|origin| same_authority(&host, &origin))
        }) && origins.next().is_none();
        let mut sites = headers.get_all("sec-fetch-site").iter();
        let valid_site = sites
            .next()
            .is_none_or(|site| site == "same-origin" || (read && site == "none"))
            && sites.next().is_none();
        valid_origin && valid_site
    } else {
        true
    };
    let mut response = if valid_browser_context {
        next.run(request).await
    } else {
        forbidden()
    };
    if api {
        response
            .headers_mut()
            .insert(header::CACHE_CONTROL, HeaderValue::from_static("no-store"));
    }
    response
        .headers_mut()
        .insert(header::X_FRAME_OPTIONS, HeaderValue::from_static("DENY"));
    response.headers_mut().insert(
        header::CONTENT_SECURITY_POLICY,
        HeaderValue::from_static(WEBUI_CSP),
    );
    response
}

fn build_router(state: StateHandle) -> Router {
    Router::new()
        .route("/api/devices", get(list_devices))
        .route("/api/device/{id}/power/on", post(device_power_on))
        .route("/api/device/{id}/power/off", post(device_power_off))
        .route(
            "/api/device/{id}/brightness/{level}",
            post(device_set_brightness),
        )
        .route(
            "/api/device/{id}/colortemp/{kelvin}",
            post(device_set_color_temperature),
        )
        .route("/api/device/{id}/color/{color}", post(device_set_color))
        .route("/api/device/{id}/scene/{scene}", post(device_set_scene))
        .route("/api/device/{id}/scenes", get(device_list_scenes))
        .route("/api/oneclicks", get(list_one_clicks))
        .route("/api/oneclick/activate/{scene}", post(activate_one_click))
        .route("/", get(redirect_to_index))
        .nest_service("/assets", ServeDir::new("assets"))
        .layer(middleware::from_fn(browser_policy))
        .with_state(state)
}

pub async fn run_http_server(state: StateHandle, bind_addr: SocketAddr) -> anyhow::Result<()> {
    let app = build_router(state);
    let listener = tokio::net::TcpListener::bind(bind_addr)
        .await
        .with_context(|| format!("run_http_server: binding to {bind_addr}"))?;
    let addr = listener.local_addr()?;
    log::info!("http server addr is {addr:?}");
    if let Err(err) = axum::serve(listener, app).await {
        log::error!("http server stopped: {err:#}");
    }

    Ok(())
}

#[cfg(test)]
#[tokio::test]
async fn error_response_preserves_status_and_json() {
    let response = bad_request("invalid color").into_response();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);
    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    assert_eq!(
        serde_json::from_slice::<serde_json::Value>(&body).unwrap(),
        serde_json::json!({"code": 400, "msg": "invalid color"})
    );
}

#[cfg(test)]
#[test]
fn test_build_router() {
    // axum has a history of chaning the URL syntax across
    // semver bumps; while that is OK, the syntax changes
    // are not caught at compile time, so we need a runtime
    // check to verify that the syntax is still good.
    // This next line will panic if axum decides that
    // the syntax is bad.
    let _ = build_router(StateHandle::default());
}

#[cfg(test)]
mod router_tests {
    use super::*;

    async fn test_server() -> (reqwest::Client, String) {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
        let url = format!("http://{}", listener.local_addr().unwrap());
        tokio::spawn(async move {
            axum::serve(listener, build_router(StateHandle::default()))
                .await
                .unwrap();
        });
        let client = reqwest::Client::builder()
            .no_proxy()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(std::time::Duration::from_secs(5))
            .build()
            .unwrap();
        (client, url)
    }

    #[tokio::test]
    async fn controls_use_post_only() {
        let (client, url) = test_server().await;
        for (path, post_status) in [
            ("/api/device/test/power/on", StatusCode::NOT_FOUND),
            ("/api/device/test/power/off", StatusCode::NOT_FOUND),
            ("/api/device/test/brightness/100", StatusCode::NOT_FOUND),
            ("/api/device/test/colortemp/3500", StatusCode::NOT_FOUND),
            ("/api/device/test/color/%23aabbcc", StatusCode::NOT_FOUND),
            ("/api/device/test/scene/test", StatusCode::NOT_FOUND),
            (
                "/api/oneclick/activate/test",
                StatusCode::INTERNAL_SERVER_ERROR,
            ),
        ] {
            let endpoint = format!("{url}{path}");
            for method in [Method::GET, Method::HEAD] {
                let response = client.request(method, &endpoint).send().await.unwrap();
                assert_eq!(response.status(), StatusCode::METHOD_NOT_ALLOWED, "{path}");
                assert_eq!(response.headers()[header::ALLOW], "POST", "{path}");
            }
            // No devices or cloud clients are configured: POST reaches the normal handler error.
            let response = client.post(&endpoint).send().await.unwrap();
            assert_eq!(response.status(), post_status, "{path}");
            let body: serde_json::Value = response.json().await.unwrap();
            assert_eq!(body["code"], post_status.as_u16(), "{path}");
        }
    }

    #[tokio::test]
    async fn browser_metadata_must_describe_the_same_origin() {
        let (client, url) = test_server().await;
        let endpoint = format!("{url}/api/device/test/power/on");
        for (origin, site) in [
            (Some("http://other.example.test"), None),
            (Some("https://127.0.0.1"), None),
            (Some("http://127.0.0.1:1"), None),
            (Some("null"), None),
            (None, Some("cross-site")),
            (Some(url.as_str()), Some("same-site")),
            (None, Some("none")),
        ] {
            let mut request = client.post(&endpoint);
            if let Some(origin) = origin {
                request = request.header(header::ORIGIN, origin);
            }
            if let Some(site) = site {
                request = request.header("sec-fetch-site", site);
            }
            let response = request.send().await.unwrap();
            assert_eq!(
                response.status(),
                StatusCode::FORBIDDEN,
                "{origin:?} {site:?}"
            );
            assert!(!response
                .headers()
                .contains_key(header::ACCESS_CONTROL_ALLOW_ORIGIN));
        }
        for site in [None, Some("same-origin")] {
            let mut request = client.post(&endpoint).header(header::ORIGIN, &url);
            if let Some(site) = site {
                request = request.header("sec-fetch-site", site);
            }
            assert_eq!(
                request.send().await.unwrap().status(),
                StatusCode::NOT_FOUND
            );
        }
        let response = client
            .post(&endpoint)
            .header(header::HOST, "[::1]:80")
            .header(header::ORIGIN, "http://[::1]")
            .send()
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn webui_and_read_api_accept_direct_addresses() {
        let (client, url) = test_server().await;
        let response = client.get(&url).send().await.unwrap();
        assert_eq!(response.status(), StatusCode::SEE_OTHER);
        assert_eq!(response.headers()[header::LOCATION], "/assets/index.html");
        let response = client
            .get(format!("{url}/assets/index.html"))
            .send()
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        assert_eq!(response.headers()[header::X_FRAME_OPTIONS], "DENY");
        assert_eq!(
            response.headers()[header::CONTENT_SECURITY_POLICY],
            WEBUI_CSP
        );

        for host in ["localhost:8056", "192.0.2.10:8056", "[::1]:8056"] {
            let response = client
                .get(format!("{url}/api/devices"))
                .header(header::HOST, host)
                .header("sec-fetch-site", "none")
                .send()
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::OK, "{host}");
            assert_eq!(response.headers()[header::CACHE_CONTROL], "no-store");
            assert_eq!(response.text().await.unwrap(), "[]");
        }
        for path in ["/", "/assets/index.html", "/api/devices"] {
            let response = client
                .get(format!("{url}{path}"))
                .header(header::HOST, "bridge.example.test")
                .send()
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::FORBIDDEN, "{path}");
        }
        for host in ["localhost:invalid", "[::1]extra:8056", "account@localhost"] {
            let response = client
                .get(format!("{url}/api/devices"))
                .header(header::HOST, host)
                .send()
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::FORBIDDEN, "{host}");
        }
    }
}
