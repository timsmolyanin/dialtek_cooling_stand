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
                    ("/devices/CoolingSystem/controls/Down limit", 0),
                    ("/devices/CoolingSystem/controls/Up limit", 0),
                    ("/devices/CoolingSystem/controls/Wait time", 0),
                    ("/devices/wb-w1/controls/28-00000ec5f529/meta/error", 0),
                    ("/devices/wb-w1/controls/28-00000ec7b1ac/meta/error", 0),
                    ("/devices/wb-w1/controls/28-00000ec76957/meta/error", 0),
                    ("/devices/wb-w1/controls/28-00000ec5e8de/meta/error", 0),
                    ("/devices/wb-w1/controls/28-00000ec7a9f9/meta/error", 0),
                    ]

"""

DT1 16-18 <16 off, 18>on

wb-w1/28-00000ec5e8de - DT6
wb-w1/28-00000ec5f529 - DT8
wb-w1/28-00000ec76957 - DT10
wb-w1/28-00000ec7a9f9 - DT1
wb-w1/28-00000ec7b1ac - DT9

/devices/+/controls/+/meta/error topics can contain a combination of values:

    r - read from device error
    w - write to device error
    p - read period miss
    "" - everything fine

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
        self.fans_on_state_count = 0
        self.temp_grow_flag = False

        self.auto_mode = False

        self.current_state = 0

        self.client_id = f"korobka-mqtt-{random.randint(0, 100)}"

    def run(self):
        while True:
            try:
                self.analyze_dt1_temp()
                time.sleep(1)
            except Exception as exc:
                logger.debug("Thread exception: ", exc)

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
            logger.debug(f"MQTT subscribe failed: ", e)
    
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
        topic_val = msg.payload.decode("utf-8")
        match topic_name[-1]:
            case "28-00000ec7a9f9":   # DT1
                try:
                    self.dt1_temperaure_value = float(topic_val)
                    self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT1 Status/on", 0)
                    if self.dt1_temperaure_value >= self.up_limit:
                        self.current_state = 1
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Temp grow flag/on", 1)
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Current state/on", "Температура выше верхнего предела!")
                        print("Температура выше верхнего предела!")
                    elif self.dt1_temperaure_value <= self.down_limit:
                        self.current_state = 2
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Current state/on", "Температура ниже нижнего предела!")
                        self.fans_on_state_count = 0
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", 0)
                        print("Температура ниже нижнего предела!")
                    elif self.dt1_temperaure_value < self.up_limit and self.dt1_temperaure_value > self.down_limit:
                        self.current_state = 0
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Current state/on", "Температура находится в установленных пределах")
                        print("Температура находится в установленных пределах")
                except Exception as exc:
                    logger.debug(f"DT1 Error. {exc}")
            case "A1_OUT":
                try:
                    relay_state = bool(int(topic_val))
                    if self.auto_mode:
                        if relay_state:
                            self.fans_on_state_count = 1
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", 1)
                except Exception as exc:
                    logger.debug(f"A1_OUT error. {exc}")
            case "A2_OUT":
                try:
                    relay_state = bool(int(topic_val))
                    if self.auto_mode:
                        if relay_state:
                            self.fans_on_state_count = 2
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", 2)
                except Exception as exc:
                    logger.debug(f"A2_OUT error. {exc}")
            case "A3_OUT":
                try:
                    relay_state = bool(int(topic_val))
                    if self.auto_mode:
                        if relay_state:
                            self.fans_on_state_count = 3
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", 3)
                except Exception as exc:
                    logger.debug(f"A3_OUT error. {exc}")
            case "D1_OUT":
                try:
                    relay_state = bool(int(topic_val))
                    if self.auto_mode:
                        if relay_state:
                            self.fans_on_state_count = 4
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", 4)
                except Exception as exc:
                    logger.debug(f"D1_OUT error. {exc}")
            case "Auto Mode":
                try:
                    self.auto_mode = bool(int(topic_val))
                    if self.auto_mode:
                        debug_str = "Включен автоматический режим"
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Debug msg/on", debug_str)
                    else:
                        debug_str = "Автоматический режим выключен"
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Debug msg/on", debug_str)
                        self.switch_off_all_fans()
                        self.fans_on_state_count = 0
                        self.time_counter = 0
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Fans ON count/on", self.fans_on_state_count)
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Counter/on", self.time_counter)
                except Exception as exc:
                    logger.debug(f"auto_mode error. {exc}")
            case "Down limit":
                try:
                    self.down_limit = float(topic_val)
                except Exception as exc:
                    logger.debug(f"down_limit error. {exc}")
            case "Up limit":
                try:
                    self.up_limit = float(topic_val)
                except Exception as exc:
                    logger.debug(f"up_limit error. {exc}")
            case "Wait time":
                try:
                    self.time_period = float(topic_val)
                except Exception as exc:
                    logger.debug(f"time_period error. {exc}")
            case "error":
                match topic_name[4]:
                    case "28-00000ec7a9f9":
                        if topic_val == "r":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT1 Status/on", 1)
                        elif topic_val == "":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT1 Status/on", 0)
                    case "28-00000ec5e8de":
                        if topic_val == "r":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT6 Status/on", 1)
                        elif topic_val == "":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT6 Status/on", 0)
                    case "28-00000ec5f529":
                        if topic_val == "r":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT8 Status/on", 1)
                        elif topic_val == "":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT8 Status/on", 0)
                    case "28-00000ec76957":
                        if topic_val == "r":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT10 Status/on", 1)
                        elif topic_val == "":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT10 Status/on", 0)
                    case "28-00000ec7b1ac":
                        if topic_val == "r":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT9 Status/on", 1)
                        elif topic_val == "":
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/DT9 Status/on", 0)

    def mqtt_publish_topic(self, topic_name, topic_value):
        """
        """
        publish.single(str(topic_name), str(topic_value), hostname=self.broker)
    
    def analyze_dt1_temp(self):
        if self.auto_mode:
            match self.current_state:
                case 0:
                    pass
                case 1:
                    if self.fans_on_state_count == 0:
                        self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 1)
                    else:
                        while self.time_counter < self.time_period:
                            if not self.auto_mode:
                                break
                            time.sleep(1)
                            self.time_counter += 1
                            self.mqtt_publish_topic("/devices/CoolingSystem/controls/Counter/on", self.time_counter)
                        self.time_counter = 0
                        self.mqtt_publish_topic("/devices/CoolingSystem/controls/Counter/on", self.time_counter)
                        match self.fans_on_state_count:
                            case 1:
                                self.mqtt_publish_topic("/devices/wb-gpio/controls/A2_OUT/on", 1)
                            case 2:
                                self.mqtt_publish_topic("/devices/wb-gpio/controls/A3_OUT/on", 1)
                            case 3:
                                self.mqtt_publish_topic("/devices/wb-gpio/controls/D1_OUT/on", 1)
                            case 4:
                                pass
                case 2:
                    self.switch_off_all_fans()
                    return
        else:
            return
    
    def switch_off_all_fans(self):
        self.mqtt_publish_topic("/devices/wb-gpio/controls/A1_OUT/on", 0)
        self.mqtt_publish_topic("/devices/wb-gpio/controls/A2_OUT/on", 0)
        self.mqtt_publish_topic("/devices/wb-gpio/controls/A3_OUT/on", 0)
        self.mqtt_publish_topic("/devices/wb-gpio/controls/D1_OUT/on", 0)


    
def test_main():
    # broker = "192.168.44.10"
    broker = "192.168.1.71"
    # broker = "127.0.0.1"
    port = 1883
    cooling_stand_simple_relay = CoolingStandSimpleRelay(mqtt_port_num=port, mqtt_broker_ip=broker, mqtt_topic_list=mqtt_topics_list)
    cooling_stand_simple_relay.mqtt_start()
    cooling_stand_simple_relay.start()

    


if __name__ == "__main__":
    test_main()
