#!/usr/bin/env python3

import paho.mqtt.client as mqtt_client
import json
import os
from time import sleep
from sys import exit

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from BAC0.core.devices.local.object import ObjectFactory
from bacpypes.basetypes import DeviceObjectPropertyReference, DailySchedule, TimeValue
from bacpypes.constructeddata import ArrayOf
from bacpypes.object import ScheduleObject
from bacpypes.primitivedata import Real
from BAC0 import lite
from BAC0.core.devices.local.models import (
    analog_input,
    analog_output,
    binary_output,
    binary_input,
)

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
RANDOM_OBJECT_COUNT = 2
# mqtt server IP
# change this to your new host IP unless the broker is deployed somewhere else
broker = 'localhost'
# mqtt server port
port = 1883
# mqtt username, if you changed the application name in TTS, please change the mqtt_username variable
mqtt_username = 'app01'
# mqtt password
# mqtt_password = 'NNSXS.LT4GXGONL5Z5PMFD7TSJKM3Q3KP3IIM7SU3ZLLA.4MIC6FOVVNG4WTPFCGX4RBE4CTEM4GOICGFTLLIFVWMQKDQYDSVA'  #change this to you new api key, this key is generated in TTS's MQTT integration page
with open('mqtt_config', 'r') as f:
    mqtt_password = str(f.readlines()[0]).strip()
# mqtt subscribe topic and publish topic
# should be something like v3/{application_id}/devices/{device_id}/up
sub_topic = 'v3/' + mqtt_username + '/devices/+/up'

device = None

# Basic configuration for the BACnet device
fake_bac0_obj = "WisGate Connect"
# fake_device_id = 999
# fake_firmware_revision = "0.1.0"
# fake_max_apdu_length = "2048"
# fake_max_segments = "2048"
# fake_bbmd_ttl = 10
fake_model_name = "RAK7391"
fake_vendor_id = 999
fake_vendor_name = "RAKWireless"


def get_IP():
    print("The value of HOME is: ", os.environ['UDP_SERVER_HOST'])


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client()
    client.username_pw_set(mqtt_username, password=mqtt_password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client):
    client.subscribe(sub_topic)
    client.on_message = on_message


def on_message(client, userdata, msg):
    # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    json_data = json.loads(msg.payload)
    temperature = json_data["uplink_message"]["decoded_payload"]["temperature_1"]
    humidity = json_data["uplink_message"]["decoded_payload"]["relative_humidity_2"]
    device["Temperature-1"].presentValue = temperature
    device["Humidity-2"].presentValue = humidity


def run_mqtt():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()


def BACnet_application():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug:
        _log.debug("initialization")
    if _debug:
        _log.debug("    - args: %r", args)

    # Define device objects
    _new_objects = analog_input(
        instance=1,
        name="Temperature-1",
        properties={"units": "degreesCelsius"},
        description="SHTC3 sensor temperature",
        presentValue=0,
    )
    analog_input(
        instance=2,
        name="Humidity-2",
        properties={"units": "percent"},
        description="SHTC3 sensor humidity",
        presentValue=0,
    )

    global device
    device = lite(ip=args.ini.address, port=47808,
                  deviceId=int(args.ini.objectidentifier),
                  modelName=fake_model_name,
                  vendorId=fake_vendor_id,
                  vendorName=fake_vendor_name,
                  localObjName=fake_bac0_obj)

    _new_objects.add_objects_to_application(device)

    if _debug:
        _log.debug("Simulation started")

    while True:
        sleep(1)


def main():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    BACnet_application()


if __name__ == "__main__":
    main()
