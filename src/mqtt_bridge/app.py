# -*- coding: utf-8 -*-
from __future__ import absolute_import

import inject
import paho.mqtt.client as mqtt
import rospy

from .bridge import create_bridge
from .mqtt_client import create_private_path_extractor
from .util import lookup_object

import netifaces

def create_config(mqtt_client, serializer, deserializer, mqtt_private_path, mac_address):
    if isinstance(serializer, basestring):
        serializer = lookup_object(serializer)
    if isinstance(deserializer, basestring):
        deserializer = lookup_object(deserializer)
    private_path_extractor = create_private_path_extractor(mqtt_private_path, mac_address)
    def config(binder):
        binder.bind('serializer', serializer)
        binder.bind('deserializer', deserializer)
        binder.bind(mqtt.Client, mqtt_client)
        binder.bind('mqtt_private_path_extractor', private_path_extractor)
    return config

##################################################################
# get mac address info
def get_wifi_device_name():
    devices = netifaces.interfaces()
    print(devices)
    # raise Exception("test exception") # test exception
    for device in devices:
        if device.lower().find('w') >= 0: # wifi device interface name has character 'w'
            return device

def get_device_mac_address(device_name):
    info = netifaces.ifaddresses(device_name)
    addr = info[netifaces.AF_PACKET][0]['addr']
    return ''.join(addr.split(':'))
##################################################################

def mqtt_bridge_node():
    # init node
    rospy.init_node('mqtt_bridge_node')

    # load parameters
    params = rospy.get_param("~", {})
    mqtt_params = params.pop("mqtt", {})
    conn_params = mqtt_params.pop("connection")
    mqtt_private_path = mqtt_params.pop("private_path", "")
    bridge_params = params.get("bridge", [])

    mac_address = ""
    try:
        mac_address = get_device_mac_address(get_wifi_device_name())
    except Exception as re:
        print('get mac address by netifaces failed.', re)

    if len(mac_address) == 0:
        print("get mac address from config file")
        mac_address = params.pop("mac")
    print("MAC ADDRESS: %s"%mac_address)

    # create mqtt client
    mqtt_client_factory_name = rospy.get_param(
        "~mqtt_client_factory", ".mqtt_client:default_mqtt_client_factory")
    mqtt_client_factory = lookup_object(mqtt_client_factory_name)
    mqtt_client = mqtt_client_factory(mqtt_params)

    # load serializer and deserializer
    serializer = params.get('serializer', 'json:dumps')
    deserializer = params.get('deserializer', 'json:loads')

    # dependency injection
    config = create_config(
        mqtt_client, serializer, deserializer, mqtt_private_path, mac_address)
    inject.configure(config)

    # configure and connect to MQTT broker
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_disconnect = _on_disconnect
    mqtt_client.connect(**conn_params)

    # configure bridges
    bridges = []
    for bridge_args in bridge_params:
        bridges.append(create_bridge(**bridge_args))

    # start MQTT loop
    mqtt_client.loop_start()

    # register shutdown callback and spin
    rospy.on_shutdown(mqtt_client.disconnect)
    rospy.on_shutdown(mqtt_client.loop_stop)
    rospy.spin()


#def _on_connect(client, userdata, flags, response_code):
def _on_connect(client, userdata, flags, reason_code, properties=None):
    rospy.loginfo('MQTT connected')


#def _on_disconnect(client, userdata, response_code):
def _on_disconnect(client, userdata, reason_code, properties=None):
    rospy.loginfo('MQTT disconnected')


__all__ = ['mqtt_bridge_node']
