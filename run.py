import paho.mqtt.client as mqtt
import json
import logging
import os

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Отримання налаштувань з options.json
with open('/data/options.json') as f:
    config = json.load(f)

logger.info(f"Loaded configuration: {json.dumps({k: v for k, v in config.items() if 'password' not in k})}")


# MQTT налаштування
mqtt_host = config.get('mqtt_host', 'core-mosquitto')  # Використовуємо core-mosquitto для вбудованого брокера
mqtt_port = config.get('mqtt_port', 1883)
mqtt_user = config.get('mqtt_user', 'mqtt_user')
mqtt_password = config.get('mqtt_password', 'Albert140')

# Callback для підключення
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected successfully to MQTT broker.")
    else:
        logger.error(f"Connection failed with code {rc}")

# Створення клієнта MQTT з новим API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Встановлення callback'ів
client.on_connect = on_connect

# Налаштування авторизації
client.username_pw_set(mqtt_user, mqtt_password)

# Підключення до MQTT брокера
try:
    logger.info(f"Attempting to connect to MQTT broker at {mqtt_host}:{mqtt_port}")
    client.connect(mqtt_host, mqtt_port, 60)
except ValueError as e:
    logger.error(f"Invalid MQTT host configuration: {e}")
    exit(1)
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)

client.loop_start()

# Основний цикл програми
try:
    while True:
        pass  # Місце для вашої основної логіки аддона
except KeyboardInterrupt:
    logger.info("Shutting down")
finally:
    client.loop_stop()
    client.disconnect()
