use crate::hass_mqtt::base::{Device, EntityConfig, Origin};
use crate::hass_mqtt::instance::{publish_entity_config, EntityInstance};
use crate::platform_api::DeviceType;
use crate::service::device::Device as ServiceDevice;
use crate::service::hass::{
    availability_topic, kelvin_to_mired, light_segment_state_topic, light_state_topic,
    topic_safe_id, HassClient,
};
use crate::service::state::StateHandle;
use async_trait::async_trait;
use serde::Serialize;
use serde_json::json;

/// <https://www.home-assistant.io/integrations/light.mqtt/#json-schema>
#[derive(Serialize, Clone, Debug)]
pub struct LightConfig {
    #[serde(flatten)]
    pub base: EntityConfig,
    pub schema: String,

    pub command_topic: String,
    /// The docs say that this is optional, but hass errors out if
    /// it is not passed
    pub state_topic: String,
    pub optimistic: bool,
    pub supported_color_modes: Vec<String>,
    /// Flag that defines if the light supports brightness.
    pub brightness: bool,
    /// Defines the maximum brightness value (i.e., 100%) of the MQTT device.
    pub brightness_scale: u32,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub icon: Option<String>,

    /// Flag that defines if the light supports effects.
    pub effect: bool,
    /// The list of effects the light supports.
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub effect_list: Vec<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    pub min_mireds: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub max_mireds: Option<u32>,

    pub payload_available: String,
}

impl LightConfig {
    pub async fn publish(&self, state: &StateHandle, client: &HassClient) -> anyhow::Result<()> {
        publish_entity_config("light", state, client, &self.base, self).await
    }
}

#[derive(Clone)]
pub struct DeviceLight {
    light: LightConfig,
    device_id: String,
    state: StateHandle,
}

#[async_trait]
impl EntityInstance for DeviceLight {
    async fn publish_config(&self, state: &StateHandle, client: &HassClient) -> anyhow::Result<()> {
        self.light.publish(state, client).await
    }

    async fn notify_state(&self, client: &HassClient) -> anyhow::Result<()> {
        if self.light.optimistic {
            return Ok(());
        }

        let device = self
            .state
            .device_by_id(&self.device_id)
            .await
            .expect("device to exist");

        match device.device_state() {
            Some(device_state) => {
                log::trace!("LightConfig::notify_state: state is {device_state:?}");

                let is_on = device_state.light_on.unwrap_or(false);

                let light_state = if is_on {
                    if device_state.kelvin == 0 {
                        json!({
                            "state": "ON",
                            "color_mode": "rgb",
                            "color": {
                                "r": device_state.color.r,
                                "g": device_state.color.g,
                                "b": device_state.color.b,
                            },
                            "brightness": device_state.brightness,
                            "effect": device_state.scene,
                        })
                    } else {
                        json!({
                            "state": "ON",
                            "color_mode": "color_temp",
                            "brightness": device_state.brightness,
                            "color_temp": kelvin_to_mired(device_state.kelvin),
                            "effect": device_state.scene,
                        })
                    }
                } else {
                    json!({"state":"OFF"})
                };

                client
                    .publish_obj(&self.light.state_topic, &light_state)
                    .await
            }
            None => {
                // TODO: mark as unavailable or something? Don't
                // want to prevent attempting to control it though,
                // as that could cause it to wake up.
                client
                    .publish_obj(&self.light.state_topic, &json!({"state":"OFF"}))
                    .await
            }
        }
    }
}

impl DeviceLight {
    pub async fn for_device(
        device: &ServiceDevice,
        state: &StateHandle,
        segment: Option<u32>,
    ) -> anyhow::Result<Self> {
        let quirk = device.resolve_quirk();
        let device_type = device.device_type();
        let lan_rgb_segment = segment.is_some() && device.lan_rgb_segment_device().is_some();

        let command_topic = match segment {
            None => format!("gv2mqtt/light/{id}/command", id = topic_safe_id(device)),
            Some(seg) if lan_rgb_segment => format!(
                "gv2mqtt/light/{id}/segments/{number}/command",
                id = topic_safe_id(device),
                number = seg + 1,
            ),
            Some(seg) => format!(
                "gv2mqtt/light/{id}/command/{seg}",
                id = topic_safe_id(device)
            ),
        };

        let icon = match segment {
            Some(_) => None,
            None if device_type == DeviceType::Light => quirk.as_ref().map(|q| q.icon.to_string()),
            None => None,
        };

        let state_topic = match segment {
            Some(seg) => light_segment_state_topic(device, seg),
            None => light_state_topic(device),
        };
        let availability_topic = availability_topic();
        let unique_id = format!(
            "gv2mqtt-{id}{seg}",
            id = topic_safe_id(device),
            seg = segment.map(|n| format!("-{n}")).unwrap_or_default()
        );

        let effect_list = if segment.is_some() {
            vec![]
        } else {
            device.scene_names.clone()
        };

        let mut supported_color_modes = vec![];

        if segment.is_some() || device.supports_rgb() {
            supported_color_modes.push("rgb".to_string());
        }

        let (min_mireds, max_mireds) = if segment.is_some() {
            (None, None)
        } else if let Some((min, max)) = device.get_color_temperature_range() {
            supported_color_modes.push("color_temp".to_string());
            // Note that min and max are swapped by the translation
            // from kelvin to mired
            (
                Some(if max == 0 {
                    0
                } else {
                    1_000_000_u32.div_ceil(max)
                }),
                Some(kelvin_to_mired(min)),
            )
        } else {
            (None, None)
        };

        let brightness = !lan_rgb_segment
            && (segment.is_some()
                || quirk.as_ref().is_some_and(|q| q.supports_brightness)
                || device
                    .http_device_info
                    .as_ref()
                    .is_some_and(|info| info.supports_brightness()));

        let name = match segment {
            Some(n) => Some(format!("Segment {:03}", n + 1)),
            None if device_type == DeviceType::Humidifier => Some("Night Light".to_string()),
            None => None,
        };

        Ok(Self {
            light: LightConfig {
                base: EntityConfig {
                    availability_topic,
                    name,
                    device_class: None,
                    origin: Origin::default(),
                    device: Device::for_device(device),
                    unique_id,
                    entity_category: None,
                    icon: None,
                },
                schema: "json".to_string(),
                command_topic,
                state_topic,
                supported_color_modes,
                brightness,
                brightness_scale: 100,
                effect: !effect_list.is_empty(),
                effect_list,
                payload_available: "online".to_string(),
                max_mireds,
                min_mireds,
                optimistic: segment.is_some(),
                icon,
            },
            device_id: device.id.to_string(),
            state: state.clone(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hass_mqtt::enumerator::enumerate_entities_for_device;
    use crate::hass_mqtt::instance::EntityList;
    use crate::service::hass::mired_to_kelvin;

    fn lan_light(sku: &str) -> ServiceDevice {
        let mut device = ServiceDevice::new(sku, "00:00:00:00:00:00:00:01");
        device.lan_device = Some(crate::lan_api::LanDevice {
            ip: "127.0.0.1".parse().unwrap(),
            device: device.id.clone(),
            sku: device.sku.clone(),
            ble_version_hard: String::new(),
            ble_version_soft: String::new(),
            wifi_version_hard: String::new(),
            wifi_version_soft: String::new(),
        });
        device
    }

    #[tokio::test]
    async fn h60c1_discovery_uses_safe_temperature_endpoints() {
        let device = lan_light("H60C1");
        assert_eq!(device.get_color_temperature_range(), Some((2700, 6500)));

        let light = DeviceLight::for_device(&device, &StateHandle::default(), None)
            .await
            .unwrap();
        let discovery = serde_json::to_value(&light.light).unwrap();
        assert_eq!(discovery["min_mireds"], 154);
        assert_eq!(discovery["max_mireds"], 370);
        assert!(discovery["supported_color_modes"]
            .as_array()
            .unwrap()
            .contains(&json!("color_temp")));
        assert!((2700..=6500).contains(&mired_to_kelvin(154)));
        assert!((2700..=6500).contains(&mired_to_kelvin(370)));
    }

    #[tokio::test]
    async fn h60c1_segment_controls_need_no_cloud_and_have_no_readback() {
        let state = StateHandle::default();
        let device = lan_light("H60C1");
        let mut entities = EntityList::new();
        enumerate_entities_for_device(&device, &state, &mut entities)
            .await
            .unwrap();
        assert_eq!(entities.len(), 6); // Diagnostic, refresh, whole light, three RGB segments.

        let segment = DeviceLight::for_device(&device, &state, Some(1))
            .await
            .unwrap();
        let config = serde_json::to_value(&segment.light).unwrap();
        assert_eq!(
            config["command_topic"],
            "gv2mqtt/light/0000000000000001/segments/2/command"
        );
        assert_eq!(config["unique_id"], "gv2mqtt-0000000000000001-1");
        assert_eq!(config["supported_color_modes"], json!(["rgb"]));
        assert_eq!(config["brightness"], false);
        assert_eq!(config["optimistic"], true);

        let other = lan_light("H60B0");
        let mut entities = EntityList::new();
        enumerate_entities_for_device(&other, &state, &mut entities)
            .await
            .unwrap();
        assert_eq!(entities.len(), 3);
        let legacy = DeviceLight::for_device(&other, &state, Some(1))
            .await
            .unwrap();
        let config = serde_json::to_value(&legacy.light).unwrap();
        assert_eq!(
            config["command_topic"],
            "gv2mqtt/light/0000000000000001/command/1"
        );
        assert_eq!(config["brightness"], true);
    }
}
