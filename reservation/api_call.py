import requests
import json

# get tables
def get_tables(restaurant_id):
    return requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/tables')

# get working days
def get_workingdays(restaurant_id):
    return requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/workingdays')

# get a restaurant example
def get_restaurant():
    return requests.get('http://127.0.0.1:5000/stub/restaurant')