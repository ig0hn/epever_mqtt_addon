import paho.mqtt.client as mqtt
import json
import logging
import os

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
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
    safe_config = {k: v for k, v in config.items() if 'password' not in k.lower()}
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
    logger.debug(f"Connect flags: {flags}")
    if rc == 0:
        logger.info("Connected successfully to MQTT broker")
        client.subscribe(mqtt_topic)
        logger.info(f"Subscribed to topic: {mqtt_topic}")
        client.publish(mqtt_topic, "Connected and ready")
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {rc}")

# Callback для отримання повідомлень
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        logger.info(f"Received message on topic {msg.topic}: {payload}")
        # Тут можна додати обробку даних від EPEVER
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    logger.info(f"Disconnected with result code: {rc}")
    if rc != 0:
        logger.error("Unexpected disconnection. Attempting to reconnect...")

# Створення клієнта MQTT
client = mqtt.Client(protocol=mqtt.MQTTv311)  # Явно вказуємо версію протоколу

# Встановлення callback'ів
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

# Налаштування авторизації
if mqtt_user and mqtt_password:
    client.username_pw_set(mqtt_user, mqtt_password)
    logger.info("Set up authentication credentials")

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
    logger.exception(e)  # Виведе повний stacktrace
finally:
    client.disconnect()
