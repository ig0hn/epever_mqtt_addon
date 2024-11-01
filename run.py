import paho.mqtt.client as mqtt
import json
import logging
import os
import time
import socket
import struct
import threading

# Налаштування логування
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clear_logs():
    try:
        # Очищаємо всі можливі місця зберігання логів
        log_paths = [
            '/data/epever_mqtt_addon.log',
            '/config/home-assistant.log',
            '/config/supervisor/logs/epever_mqtt_addon.log'
        ]
        for log_path in log_paths:
            try:
                open(log_path, 'w').close()
                logger.info(f"Cleared log file: {log_path}")
            except Exception as e:
                logger.warning(f"Could not clear log file {log_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")

def load_config():
    config_path = '/data/options.json'
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at {config_path}")
        exit(1)

    try:
        with open(config_path) as f:
            config = json.load(f)
        
        safe_config = {k: v for k, v in config.items() if 'password' not in k.lower()}
        logger.info(f"Loaded configuration: {json.dumps(safe_config)}")
        
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        exit(1)

class EpeverReader:
    def __init__(self, host='192.168.0.100', port=502):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Epever at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Epever: {e}")
            self.sock = None

    def read_registers(self, start_register, num_registers):
        if not self.sock:
            self.connect()
            if not self.sock:
                return None

        try:
            # Формуємо Modbus запит
            request = struct.pack('>HHHBBHH',
                0x0001,         # Transaction ID
                0x0000,         # Protocol ID
                0x0006,         # Length
                0x01,           # Unit ID
                0x03,           # Function code (Read Holding Registers)
                start_register, # Starting address
                num_registers   # Quantity of registers
            )
            
            self.sock.send(request)
            response = self.sock.recv(1024)
            
            if len(response) < 9:
                logger.error("Response too short")
                return None
                
            byte_count = response[8]
            data_bytes = response[9:9+byte_count]
            
            # Розпаковуємо дані залежно від кількості регістрів
            format_string = '>' + 'H' * (byte_count // 2)
            values = struct.unpack(format_string, data_bytes)
            
            return values
            
        except Exception as e:
            logger.error(f"Error reading registers: {e}")
            self.sock = None
            return None

    def read_data(self):
        try:
            # Читаємо основні параметри (0x3100-0x3108)
            rated_data = self.read_registers(0x3100, 9)
            if not rated_data:
                return None

            # Читаємо додаткові параметри (0x3110-0x3114)
            status_data = self.read_registers(0x3110, 5)
            if not status_data:
                return None

            data = {
                'pv_voltage': rated_data[0] * 0.01,
                'pv_current': rated_data[1] * 0.01,
                'pv_power': rated_data[2],
                'battery_voltage': rated_data[3] * 0.01,
                'battery_current': rated_data[4] * 0.01,
                'battery_power': rated_data[5],
                'load_voltage': rated_data[6] * 0.01,
                'load_current': rated_data[7] * 0.01,
                'load_power': rated_data[8],
                'battery_temperature': status_data[0] * 0.01,
                'controller_temperature': status_data[1] * 0.01,
                'battery_capacity': status_data[2],
                'battery_status': status_data[3],
                'charging_status': status_data[4]
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error reading Epever data: {e}")
            return None

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logger.info("Connected successfully to MQTT broker")
        client.subscribe(mqtt_topic)
        logger.info(f"Subscribed to topic: {mqtt_topic}")
        # Публікуємо повідомлення про готовність
        client.publish(f"{mqtt_topic}/status", "online", retain=True)
    else:
        logger.error(f"Failed to connect to MQTT broker with code: {reason_code}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        logger.info(f"Received message on topic {msg.topic}: {payload}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")

def on_disconnect(client, userdata, rc, properties=None):
    logger.info(f"Disconnected with result code: {rc}")
    if rc != 0:
        logger.error("Unexpected disconnection. Attempting to reconnect...")

def create_mqtt_client():
    # Створюємо клієнта з унікальним ID
    client = mqtt.Client(
        client_id=f"epever_client_{int(time.time())}",
        protocol=mqtt.MQTTv5,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )
    
    # Встановлюємо callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    # Встановлюємо last will message
    client.will_set(f"{mqtt_topic}/status", "offline", retain=True)
    
    return client

def publish_epever_data(client, epever, mqtt_topic):
    while True:
        try:
            data = epever.read_data()
            if data:
                # Публікуємо кожне значення в окремий топік
                for key, value in data.items():
                    topic = f"{mqtt_topic}/{key}"
                    client.publish(topic, value, retain=True)
                logger.info(f"Published Epever data: {data}")
            else:
                logger.warning("Failed to read Epever data")
        except Exception as e:
            logger.error(f"Error in publish loop: {e}")
        
        time.sleep(10)  # Затримка між зчитуваннями

if __name__ == "__main__":
    # Очищаємо логи при старті
    clear_logs()
    
    # Завантажуємо конфігурацію
    config = load_config()
    
    # MQTT налаштування
    mqtt_host = config.get('mqtt_host', 'core-mosquitto')
    mqtt_port = int(config.get('mqtt_port', 1883))
    mqtt_user = config.get('mqtt_user')
    mqtt_password = config.get('mqtt_password')
    mqtt_topic = config.get('mqtt_topic', 'home/epever-solar/epever/data')
    
    # Epever налаштування
    epever_host = config.get('epever_host', '192.168.0.100')
    epever_port = int(config.get('epever_port', 502))

    # Створюємо об'єкт для роботи з Epever
    epever = EpeverReader(epever_host, epever_port)
    
    # Створюємо MQTT клієнта
    client = create_mqtt_client()

    # Налаштування авторизації
    if mqtt_user and mqtt_password:
        client.username_pw_set(mqtt_user, mqtt_password)
        logger.info("Set up authentication credentials")

    # Підключення до MQTT брокера з повтором
    max_retries = 5
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to MQTT broker at {mqtt_host}:{mqtt_port} (attempt {attempt + 1}/{max_retries})")
            client.connect(mqtt_host, mqtt_port, 60)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                time.sleep(retry_delay)
            else:
                logger.error(f"All connection attempts failed: {e}")
                exit(1)

    # Запускаємо потік для публікації даних
    data_thread = threading.Thread(
        target=publish_epever_data,
        args=(client, epever, mqtt_topic),
        daemon=True
    )
    data_thread.start()

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error("Unexpected error")
        logger.exception(e)
    finally:
        client.publish(f"{mqtt_topic}/status", "offline", retain=True)
        client.disconnect()
