#!/usr/bin/env python3

"""
This sample application shows how to extend one of the basic objects, an Analog
Value Object in this case, to provide a present value. This type of code is used
when the application is providing a BACnet interface to a collection of data.
It assumes that almost all of the default behaviour of a BACpypes application is
sufficient.
"""

import paho.mqtt.client as mqtt_client
import json
import os

from bacpypes.debugging import bacpypes_debugging, ModuleLogger
from bacpypes.consolelogging import ConfigArgumentParser

from bacpypes.core import run

from bacpypes.primitivedata import Real
from bacpypes.object import AnalogValueObject, Property, register_object_type
from bacpypes.errors import ExecutionError

from bacpypes.app import BIPSimpleApplication
from bacpypes.local.device import LocalDeviceObject

# some debugging
_debug = 0
_log = ModuleLogger(globals())

# settings
RANDOM_OBJECT_COUNT = 2
# mqtt server IP
broker = 'localhost'  # change this to your new host IP if the broker is deployed somewhere else
# mqtt server port
port = 1883
# mqtt username
mqtt_username = 'app01'
# mqtt password
mqtt_password = 'NNSXS.LT4GXGONL5Z5PMFD7TSJKM3Q3KP3IIM7SU3ZLLA.4MIC6FOVVNG4WTPFCGX4RBE4CTEM4GOICGFTLLIFVWMQKDQYDSVA'  #change this to you new api key, this key is generated in TTS's MQTT integration page
# mqtt subscribe topic and publish topic
# should be something like v3/{application_id}/devices/{device_id}/up
sub_topic = 'v3/app01/devices/+/up'
temperature = None


#
#   SensorValueProperty
#

class SensorValueProperty(Property):

    def __init__(self, identifier):
        if _debug: SensorValueProperty._debug("__init__ %r", identifier)
        Property.__init__(self, identifier, Real, default=0.0, optional=True, mutable=False)

    def ReadProperty(self, obj, arrayIndex=None):
        if _debug: SensorValueProperty._debug("ReadProperty %r arrayIndex=%r", obj, arrayIndex)
        # access an array
        if arrayIndex is not None:
            raise ExecutionError(errorClass='property', errorCode='propertyIsNotAnArray')
        # return sensor readings
        value = temperature
        print("Sending temperature reading:" + str(value) + "°C out via BACnet IP")
        if _debug: SensorValueProperty._debug("    - value: %r", value)
        return value

    def WriteProperty(self, obj, value, arrayIndex=None, priority=None, direct=False):
        if _debug: SensorValueProperty._debug("WriteProperty %r %r arrayIndex=%r priority=%r direct=%r", obj, value,
                                              arrayIndex, priority, direct)
        raise ExecutionError(errorClass='property', errorCode='writeAccessDenied')

bacpypes_debugging(SensorValueProperty)

#
#   Random Value Object Type
#

class SensorAnalogValueObject(AnalogValueObject):
    properties = [
        SensorValueProperty('presentValue'),
    ]

    def __init__(self, **kwargs):
        if _debug: SensorAnalogValueObject._debug("__init__ %r", kwargs)
        AnalogValueObject.__init__(self, **kwargs)


bacpypes_debugging(SensorAnalogValueObject)
register_object_type(SensorAnalogValueObject)


def get_IP():
    # print("The keys and values of all environment variables:")
    # for key in os.environ:
    #     print(key, '=>', os.environ[key])

    # Print the value of the particular environment variable
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
    # def on_message(client, userdata, msg):
    #     # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    #     json_data = json.loads(msg.payload)
    #     relative_humidity = json_data["uplink_message"]["decoded_payload"]["relative_humidity_2"]
    #     global temperature
    #     temperature = json_data["uplink_message"]["decoded_payload"]["temperature_1"]
    #     print(temperature)
    client.subscribe(sub_topic)
    client.on_message = on_message


def on_message(client, userdata, msg):
    # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    json_data = json.loads(msg.payload)
    relative_humidity = json_data["uplink_message"]["decoded_payload"]["relative_humidity_2"]
    global temperature
    temperature = json_data["uplink_message"]["decoded_payload"]["temperature_1"]
    print(temperature)


def run_mqtt():
    client = connect_mqtt()
    subscribe(client)

    client.loop_stop()


def BACnet_application():
    # parse the command line arguments
    args = ConfigArgumentParser(description=__doc__).parse_args()

    if _debug: _log.debug("initialization")
    if _debug: _log.debug("    - args: %r", args)

    # make a device object
    this_device = LocalDeviceObject(
        objectName=args.ini.objectname,
        objectIdentifier=('device', int(args.ini.objectidentifier)),
        maxApduLengthAccepted=int(args.ini.maxapdulengthaccepted),
        segmentationSupported=args.ini.segmentationsupported,
        vendorIdentifier=int(args.ini.vendoridentifier),
    )

    # make a sample application
    this_application = BIPSimpleApplication(this_device, args.ini.address)
    print("A sample BACnet application is created...")

    # make some input objects
    ravo = SensorAnalogValueObject(objectIdentifier=('analogValue', 1), objectName='Temperature-%d' % (1,), )
    print("It will read temperature inputs from LoRaWAN nodes via MQTT, and then send it out via BACnet IP...")
    _log.debug("    - ravo: %r", ravo)
    this_application.add_object(ravo)

    # make sure they are all there
    _log.debug("    - object list: %r", this_device.objectList)
    _log.debug("running")
    run()
    _log.debug("fini")


def main():
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    BACnet_application()


if __name__ == "__main__":
    main()
