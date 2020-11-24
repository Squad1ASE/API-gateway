import requests
import json
import os

from requests import Response

API_GATEWAY_SERVICE = 'http://127.0.0.1:5000/'
#API_GATEWAY_SERVICE = os.environ['API_GATEWAY_SERVICE']

# get a restaurant example
def get_restaurant(restaurant_id):
    reply = object
    try:
        reply = requests.get(API_GATEWAY_SERVICE+'stub/restaurant', timeout=10) #todo
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        reply = Response()
        reply.status_code = 500
    finally:
        return reply

def get_restaurant_name(restaurant_id):
    reply = object
    try:
        reply=requests.get(API_GATEWAY_SERVICE+'stub/restaurant/name', timeout=10)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        reply = Response()
        reply.status_code = 500
    finally:
        return reply

def put_notification(notification):
    reply = object
    try:
        reply = requests.put(API_GATEWAY_SERVICE+'users/notification', json=json.dumps(notification), timeout=10)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        reply = Response()
        reply.status_code = 500
    finally:
        return reply