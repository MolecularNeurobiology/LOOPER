import paho.mqtt.publish as publish

MQTT_SERVER = "128.249.96.51"
MQTT_PATH = "test_channel"

publish.single(MQTT_PATH, "hello", hostname = MQTT_SERVER)
