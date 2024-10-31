import paho.mqtt.client as mqtt
import json
import logging
import os

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Перевірка наявності файлу конфігурації
config_path = '/data/options.json'
if not os.path.exists(config_path):
    logger.error(f"Configuration file not found at {config_path}")
    exit(1)

try:
    # Отримання налаштувань з options.json
    with open(config_path) as f:
        config = json.load(f)
    
    # Логування завантаженої конфігурації (без паролю)
    safe_config = {k: v for k, v in config.items() if 'password' not in k}
    logger.info(f"Loaded configuration: {json.dumps(safe_config)}")
    
    # MQTT налаштування
    mqtt_host = config['mqtt_host']
    mqtt_port = int(config['mqtt_port'])
    mqtt_user = config['mqtt_user']
    mqtt_password = config['mqtt_password']
    mqtt_topic = config['mqtt_topic']
    
except KeyError as e:
    logger.error(f"Missing required configuration key: {e}")
    exit(1)
except json.JSONDecodeError as e:
    logger.error(f"Invalid JSON in configuration file: {e}")
    exit(1)
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    exit(1)

# Callback для підключення
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected successfully to MQTT broker")
        client.subscribe(mqtt_topic)
        logger.info(f"Subscribed to topic: {mqtt_topic}")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

# Callback для отримання повідомлень
def on_message(client, userdata, msg):
    logger.info(f"Received message on topic {msg.topic}: {msg.payload.decode()}")

# Створення клієнта MQTT
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

# Встановлення callback'ів
client.on_connect = on_connect
client.on_message = on_message

# Налаштування авторизації
if mqtt_user and mqtt_password:
    client.username_pw_set(mqtt_user, mqtt_password)

# Підключення до MQTT брокера
try:
    logger.info(f"Attempting to connect to MQTT broker at {mqtt_host}:{mqtt_port}")
    client.connect(mqtt_host, mqtt_port, 60)
except Exception as e:
    logger.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)

# Запуск головного циклу
try:
    client.loop_forever()
except KeyboardInterrupt:
    logger.info("Shutting down")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    client.disconnect()
