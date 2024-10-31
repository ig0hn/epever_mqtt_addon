import os
import paho.mqtt.client as mqtt

# Отримайте конфігурації з опцій аддона
mqtt_host = os.getenv("MQTT_HOST")
mqtt_port = int(os.getenv("MQTT_PORT", 1883))
mqtt_user = os.getenv("MQTT_USER")
mqtt_password = os.getenv("MQTT_PASSWORD")
mqtt_topic = os.getenv("MQTT_TOPIC")

# Функція для обробки підключення
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(mqtt_topic)

# Функція для обробки повідомлень
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}\nMessage: {msg.payload.decode()}")

# Налаштування MQTT-клієнта
client = mqtt.Client()
client.username_pw_set(mqtt_user, mqtt_password)
client.on_connect = on_connect
client.on_message = on_message

# Підключення до брокера
client.connect(mqtt_host, mqtt_port, 60)

# Запуск клієнта
client.loop_forever()
