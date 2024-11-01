# Виберіть базовий образ
FROM alpine:3.13

# Встановіть необхідні пакети
RUN apk add --no-cache python3 py3-pip

# Встановіть бібліотеку paho-mqtt для роботи з MQTT
RUN pip3 install paho-mqtt

# Створіть директорію для даних
RUN mkdir -p /data

# Скопіюйте скрипт аддона до контейнера
COPY run.py /run.py

# Вкажіть команду для запуску скрипта
CMD ["python3", "/run.py"]

# Labels для Home Assistant
LABEL \
    io.hass.version="1.0" \
    io.hass.type="addon" \
    io.hass.arch="armhf|armv7|aarch64|amd64|i386"
    
RUN mkdir -p /config/supervisor/logs
RUN touch /config/supervisor/logs/epever_mqtt_addon.log
RUN truncate -s 0 /config/supervisor/logs/epever_mqtt_addon.log
