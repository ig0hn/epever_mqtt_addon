# EPEVER MQTT Addon

This addon monitors EPEVER MQTT data and integrates with Home Assistant.

## Installation

1. In Home Assistant, navigate to Settings -> Add-ons -> Add-on Store
2. Click the menu (⋮) in the top right
3. Select "Repositories"
4. Add this repository URL: `https://github.com/ig0hn/epever_mqtt_addon`
5. Click "Add"
6. Find the "EPEVER MQTT Monitor" addon in the list and click "Install"

## Configuration

The following configuration options are available:

| Option | Description |
|--------|-------------|
| mqtt_host | MQTT broker host address |
| mqtt_port | MQTT broker port (default: 1883) |
| mqtt_user | MQTT username |
| mqtt_password | MQTT password |
| mqtt_topic | MQTT topic for EPEVER data |

Example configuration:
```yaml
mqtt_host: "192.168.0.95"
mqtt_port: 1883
mqtt_user: "mqtt_user"
mqtt_password: "your_password"
mqtt_topic: "home/epever-solar/epever/data"
