from typing import Dict, Callable

import paho.mqtt.client as mqtt

import rospy


def default_mqtt_client_factory(params: Dict) -> mqtt.Client:
    """ MQTT Client factory """
    # create client
    client_params = params.get('client', {})
    client = mqtt.Client(**client_params)

    # configure tls
    tls_params = params.get('tls', {})
    if tls_params:
        tls_insecure = tls_params.pop('tls_insecure', False)
        client.tls_set(**tls_params)
        client.tls_insecure_set(tls_insecure)

    # configure username and password
    account_params = params.get('account', {})
    if account_params:
        client.username_pw_set(**account_params)

    # configure message params
    message_params = params.get('message', {})
    if message_params:
        inflight = message_params.get('max_inflight_messages')
        if inflight is not None:
            client.max_inflight_messages_set(inflight)
        queue_size = message_params.get('max_queued_messages')
        if queue_size is not None:
            client.max_queued_messages_set(queue_size)
        retry = message_params.get('message_retry')
        if retry is not None:
            client.message_retry_set(retry)

    # configure userdata
    userdata = params.get('userdata', {})
    if userdata:
        client.user_data_set(userdata)

    # configure will params
    mac_address = rospy.get_param('mac_address')    # get params initialized
    mqtt_private_path = rospy.get_param('mqtt_private_path')
    will_params = params.get('will', {})
    will_topic = will_params['topic']               # 
    will_payload = will_params['payload']
    updated = False
    if will_topic.find('$mac'):
        result = will_topic.replace('$mac', mac_address)
        updated = True
    if result.startswith('~'):
        result = result.replace('~', mqtt_private_path)
        updated = True
    if updated:
        will_params.update({'topic': result})
    # print(result)
    updated = False
    if will_payload.find('$mac'):
        result = will_payload.replace('$mac', mac_address)
        updated = True
    if updated:
        will_params.update({'payload': result})
    # print(result)
    print(will_params)
    if will_params:
        client.will_set(**will_params)

    return client


def create_private_path_extractor(mqtt_private_path: str, mac_address: str) -> Callable[[str], str]:
    def extractor(topic_path):
        if topic_path.startswith('~/') & topic_path.endswith('$mac'):
            print('{}/{}/{}'.format(mqtt_private_path, topic_path[2:-5], mac_address))
            return '{}/{}/{}'.format(mqtt_private_path, topic_path[2:-5], mac_address)
        else:
            print('{}/{}'.format(mqtt_private_path, topic_path[2:]))
            return '{}/{}'.format(mqtt_private_path, topic_path[2:])
        return topic_path
    return extractor


__all__ = ['default_mqtt_client_factory', 'create_private_path_extractor']
