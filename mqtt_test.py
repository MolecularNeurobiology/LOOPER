import paho.mqtt.publish as publish

MQTT_SERVER = "10.51.136.152"
MQTT_PATH = "test_channel"

publish.single(MQTT_PATH, "hello", hostname = MQTT_SERVER)
