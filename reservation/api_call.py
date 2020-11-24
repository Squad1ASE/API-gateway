import requests
import json

# get tables
def get_tables(restaurant_id):
    return requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/tables')

# get working days
def get_workingdays(restaurant_id):
    return requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/workingdays')

# get a restaurant example
def get_restaurant(restaurant_id):
    return requests.get('http://127.0.0.1:5000/stub/restaurant')

def get_restaurant_name(restaurant_id):
    return requests.get('http:127.0.0.1:5000/stub/restaurant/name')

def put_notification(notification):
    return requests.put('http://127.0.0.1:5000/users/notification', json=json.dumps(notification))