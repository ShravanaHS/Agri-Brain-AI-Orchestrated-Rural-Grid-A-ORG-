import paho.mqtt.client as mqtt
import time

def on_publish(client, userdata, mid, reason_code=None, properties=None):
    print("mid: " + str(mid))

c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
c.on_publish = on_publish
c.tls_set()
c.username_pw_set('agribrain', '#Shs_2838')
c.connect('33712c7cb7174024b63e809028448b03.s1.eu.hivemq.cloud', 8883)

c.loop_start()
payload = '{"query":"How do I grow tomatoes?","source":"web"}'
print("Publishing...")
info = c.publish('agribrain_shravan/voice_command', payload, qos=1)
info.wait_for_publish()
print("Published!")
time.sleep(2)
c.disconnect()
c.loop_stop()
