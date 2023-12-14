#!/root/wk/py310/bin/python


import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt

import random

import time

from loguru import logger

from threading import Thread

mqtt_topics_list = [("/devices/wb-w1/controls/28-00000ec5f529", 0),
                    ("/devices/wb-w1/controls/28-00000ec7b1ac", 0),
                    ("/devices/wb-w1/controls/28-00000ec76957", 0),
                    ("/devices/wb-w1/controls/28-00000ec5e8de", 0),
                    ("/devices/wb-w1/controls/28-00000ec7a9f9", 0),
                    ("/devices/wb-gpio/controls/A1_OUT", 0),
                    ("/devices/wb-gpio/controls/A2_OUT", 0),
                    ("/devices/wb-gpio/controls/A3_OUT", 0),
                    ("/devices/wb-gpio/controls/D1_OUT", 0),
                    ("/devices/CoolingSystem/controls/Auto Mode", 0),
                    ]

"""

DT1 16-18 <16 off, 18>on

wb-w1/28-00000ec5e8de - DT6
wb-w1/28-00000ec5f529 - DT8
wb-w1/28-00000ec76957 - DT10
wb-w1/28-00000ec7a9f9 - DT1
wb-w1/28-00000ec7b1ac - DT9

"""

logger.add("debug.log", format="{time} {level} {message}", level="DEBUG")


class CoolingStandSimpleRelay(Thread):
    def __init__(self, mqtt_port_num: int, mqtt_broker_ip: str, mqtt_topic_list: list, parent=None):
        super(CoolingStandSimpleRelay, self).__init__(parent)
        self.broker = mqtt_broker_ip
        self.port = mqtt_port_num
        self.mqtt_topic_list = mqtt_topic_list

        self.time_counter = 0
        self.time_period = 60

        self.up_limit = 18
        self.down_limit = 16

        self.dt1_temperaure_value = 0
        self.vent_on_state_count = 0
        self.temp_grow_flag = False

        self.auto_mode = False

        self.client_id = f"korobka-mqtt-{random.randint(0, 100)}"

    def run(self):
        while True:
            try:
                self.analyze_dt1_temp()
            except Exception as exc:
                print("mqtt thread run", exc)

    def connect_mqtt(self, whois: str) -> mqtt:
        """
        The function `connect_mqtt` connects to an MQTT broker and returns the MQTT client.
        :return: an instance of the MQTT client.
        """
        logger.debug(f"MQTT client in {whois} started connect to broker")
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.debug(f"{whois} Connected to MQTT Broker!")
            else:
                logger.debug(f"{whois} Failed to connect, return code {rc}")

        mqtt_client = mqtt.Client(self.client_id)
        mqtt_client.on_connect = on_connect
        mqtt_client.connect(self.broker, self.port)
        return mqtt_client
    
    def subscribe(self, client: mqtt):
        """
        The `subscribe` function subscribes the client to two MQTT topics and sets the `on_message` callback
        function to `self.on_message`.
        
        :param client: The `client` parameter is an instance of the MQTT client that is used to connect to
        the MQTT broker and subscribe to topics
        :type client: mqtt
        """
        try:
            client.subscribe(self.mqtt_topic_list) 
            client.on_message = self.on_message
        except Exception as e:
            print(e)
    
    def mqtt_start(self):
        """
        The function `mqtt_start` starts the MQTT client, connects to the MQTT broker, subscribes to
        topics, and starts the client's loop.
        """
        client = self.connect_mqtt("Cooling system")
        self.subscribe(client)
        client.loop_start()

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        topic_name = msg.topic.split("/")
        topic_val = float(msg.payload.decode("utf-8"))
        debug_str = ""
        match topic_name[-1]:
            case "28-00000ec7a9f9":   # DT1
                self.dt1_temperaure_value = topic_val
                if self.auto_mode:
                    print("Включен автоматический режим")
                    debug_str = "Включен автоматический режим"
                    self.mqtt_publish_topic("/devices/CoolingSystem/controls/Auto Mode/on", debug_str)
                    self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 1)
                    if topic_val >= self.up_limit:
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 1)
                        self.temp_grow_flag = True
                    elif topic_val <= self.down_limit:
                        self.temp_grow_flag = False
                        self.vent_on_state_count = 0
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A2_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A3_OUT/on", 0)
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/D1_OUT/on", 0)
                else:
                    print("Автоматический режим выключен")
                    return
            case "A1_OUT":
                print(topic_name, topic_val, type(topic_val))
                if self.auto_mode:
                    if topic_val == 1:
                        self.vent_on_state_count += 1
                else:
                    return
            case "A2_OUT":
                if self.auto_mode:
                    if topic_val == 1:
                        self.vent_on_state_count += 1
                else:
                    return
            case "A3_OUT":
                if self.auto_mode:
                    if topic_val == 1:
                        self.vent_on_state_count += 1
                else:
                    return
            case "D1_OUT":
                if self.auto_mode:
                    if topic_val == 1:
                        self.vent_on_state_count += 1
                else:
                    return
            case "Auto Mode":
                self.auto_mode = bool(int(topic_val))

    def mqtt_publish_topic(self, topic_name, topic_value):
        """
        """
        publish.single(str(topic_name), str(topic_value), hostname=self.broker)
    
    def analyze_dt1_temp(self):
        if self.auto_mode:
            if self.temp_grow_flag:
                while self.time_counter < self.time_period:
                    time.sleep(1)
                    self.time_counter += 1
                self.time_counter = 0
                if self.dt1_temperaure_value > self.up_limit:
                    match self.vent_on_state_count:
                        case 1:
                            self.mqtt_publish_topic("/devices/wb-gpio/controls/A2_OUT/on", 1)
                        case 2:
                            self.mqtt_publish_topic("/devices/wb-gpio/controls/A3_OUT/on", 1)
                        case 3:
                            self.mqtt_publish_topic("/devices/wb-gpio/controls/D1_OUT/on", 1)
                else:
                    return
        else:
            return


    
def test_main():
    broker = "192.168.44.10"
    # broker = "127.0.0.1"
    port = 1883
    cooling_stand_simple_relay = CoolingStandSimpleRelay(mqtt_port_num=port, mqtt_broker_ip=broker, mqtt_topic_list=mqtt_topics_list)
    cooling_stand_simple_relay.mqtt_start()
    cooling_stand_simple_relay.start()



if __name__ == "__main__":
    test_main()
