# Device support

Support depends on capabilities exposed by Govee through LAN, the Platform API
or undocumented cloud/IoT APIs. BLE-only devices are unsupported.
Only LAN functions work without internet access; effects, segments and scenes
may require additional cloud access.

| Device family | Support |
| --- | --- |
| Wi-Fi lights and LED strips | LAN where LAN Control is available; additional functions through Platform API and IoT |
| Humidifiers | Model-dependent Platform API functions; additional night-light support for H7160 |
| Kettles | Existing support for H7171/H7173 |
| Heaters, fans, purifiers | Existing support includes H7101, H7102, H7111, H7121, H7130, H7131, H713A, H7135 |
| Plugs | Platform API support with model-specific limitations, such as H5082 |

These entries describe existing integrations, not full acceptance testing for
every model or firmware. Device-specific exceptions are in
`src/service/quirks.rs`. Include the model, connection method, fork version and
sanitized logs in bug reports.
