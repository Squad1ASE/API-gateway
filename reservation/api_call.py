import requests
import json
import os

#API_GATEWAY_SERVICE = 'http://127.0.0.1:5000/'
API_GATEWAY_SERVICE = os.environ['API_GATEWAY_SERVICE']

# get tables
def get_tables(restaurant_id):
    return requests.get(API_GATEWAY_SERVICE+'restaurants/'+str(restaurant_id)+'/tables')

# get working days
def get_workingdays(restaurant_id):
    return requests.get(API_GATEWAY_SERVICE+'restaurants/'+str(restaurant_id)+'/workingdays')

# get a restaurant example
def get_restaurant(restaurant_id):
    return requests.get(API_GATEWAY_SERVICE+'stub/restaurant')

def get_restaurant_name(restaurant_id):
    return requests.get(API_GATEWAY_SERVICE+'stub/restaurant/name')

def put_notification(notification):
    return requests.put(API_GATEWAY_SERVICE+'users/notification', json=json.dumps(notification))