import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

from threading import Thread

mqtt_topics_list = [("/devices/wb-w1/controls/28-00000ec5f529", 0),
                    ("/devices/wb-w1/controls/28-00000ec7b1ac", 0),
                    ("/devices/wb-w1/controls/28-00000ec76957", 0),
                    ("/devices/wb-w1/controls/28-00000ec5e8de", 0),
                    ("/devices/wb-w1/controls/28-00000ec7a9f9", 0),]



"""

DT1 16-18 <16 off, 18>on

"""

class MQTTSubscriberThread(Thread):
    def __init__(self, mqtt_client, host, port, topics_list, comport=None, parent=None):
        super(MQTTSubscriberThread, self).__init__(parent)
        self.mqtt_client = mqtt_client
        self.host = host
        self.port = port
        self.topics_list = topics_list
        # self.logger = logger
        self.mqtt_client.connect(self.host, self.port, 60)
        # self.logger.info("MQTT")

        self.comport = comport

        self.data_buff = list()
        self.dt = 1
        self.experimental_coef = 1
        self.count_of_switched_on_vent = 0
        self.setpoint = 17

        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        print(self.topics_list)
        self.mqtt_client.subscribe(self.topics_list)

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        topic_name = msg.topic.split("/")
        topic_val = msg.payload.decode("utf-8")
        # print(topic_name, topic_val)
        match topic_name[-1]:
            case "28-00000ec7a9f9":     # DT1
                print(topic_name, topic_val)
                self.data_buff.append(float(topic_val))
                if len(self.data_buff) == 2:
                    state = self.calculate_relay_state(self.data_buff, 18)
                    self.data_buff.clear()
                    if state:
                         self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 1)
                    else:
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A2_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A3_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/D1_OUT/on", 0)
    
    def get_derivative(self, buff: list, dt:float):
        prev_temp = buff[0]
        current_temp = buff[1]
        return round(((current_temp - prev_temp) / dt), 5)    # производная от величины (величина/секунду)

    def calculate_relay_state(self, buff, setpoint):
        hysteresis = 2
        deriv = self.get_derivative(self.data_buff, self.dt)
        print("temp_buff: ", self.data_buff)
        print("derivative: ", deriv)
        signal = buff[1] + deriv * self.experimental_coef;
        a = signal - setpoint - hysteresis / 2
        b = signal - setpoint + hysteresis / 2
        f_part = self.my_sign(a)
        s_part = self.my_sign(b)
        f = (f_part + s_part) / 2
        print("signal: ", f)
        return bool(int(f))


    def mqtt_publish_topic(self, topic_name, topic_value):
        """
        """
        publish.single(str(topic_name), str(topic_value), hostname=self.host)

    def run(self):
        while True:
            try:
                self.mqtt_client.loop_forever()
            except Exception as exc:
                print("mqtt thread run", exc)
    
    def my_sign(self, x):
        return (x > 0) - (x < 0)



def _test_main():
    client = mqtt.Client()
    mqtt_test = MQTTSubscriberThread(client, "192.168.44.10", 1883, mqtt_topics_list)
    mqtt_test.start()
    pass


if __name__ == "__main__":
    _test_main()
