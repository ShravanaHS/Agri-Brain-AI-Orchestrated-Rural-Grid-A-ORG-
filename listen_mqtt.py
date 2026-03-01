import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected")
    client.subscribe("agribrain_shravan/#")

def on_message(client, userdata, msg):
    print(f"TOPIC: {msg.topic}\nPAYLOAD: {msg.payload.decode('utf-8')}\n")

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_connect = on_connect
c.on_message = on_message
c.tls_set()
c.username_pw_set('agribrain', '#Shs_2838')
c.connect('33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud', 8883)
c.loop_forever()
