from flask import Blueprint, redirect, render_template, request, make_response, jsonify, Response

from monolith.database import db, User, Review, Restaurant, Like, WorkingDay, Table, Dish, Seat, Reservation, Quarantine, Notification
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import (DishForm, UserForm, RestaurantForm, ReservationPeopleEmail, 
                            SubReservationPeopleEmail, ReservationRequest, RestaurantSearch, 
                            EditRestaurantForm, ReviewForm )
from monolith.views import auth
import datetime
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
import ast
import time
import datetime
from time import mktime
from datetime import timedelta
from sqlalchemy import or_
import json
import requests

api_stub = Blueprint('api_stub', __name__)

@api_stub.route('/stub/send_reservation')
def send_reservation():
    '''
    example = Reservation()
    example.booker_id = 1
    example.restaurant_id = 1
    example.table_id = 1
    example.date = datetime.datetime.strptime("10/10/2020 12:00", "%d/%m/%Y %H:%M")
    example.cancelled = False
    '''
    temp_dict = dict(
                    
                    booker_id=2,
                    restaurant_id=2,
                    table_id=2,                    
                    date='10/10/2020 12:00',#datetime.datetime.strftime("10/10/2020 12:00", "%d/%m/%Y %H:%M"),
                    cancelled=False
                )
    #TODO: pass json
    return requests.put("http://127.0.0.1:5000/reservations/users/1", data=json.dumps(temp_dict)) 

import json

def wday_to_json(wday):
    #w_dict = dict(
    #    restaurant_id = wday.restaurant_id,
    #    day = int(str(wday.day)),
    #    work_shifts = wday.work_shifts
    #)
    w_dict = {
        'restaurant_id':wday.restaurant_id,
        'day':int(str(wday.day)),
        'work_shifts':wday.work_shifts
    }
    return w_dict

def table_to_json(table):
    t_dict = {
        'id' : table.id,
        'restaurant_id' : table.restaurant_id,
        'table_name' : table.table_name,
        'capacity' : table.capacity
    }
    return t_dict

@api_stub.route('/restaurants/<restaurant_id>/workingdays', methods=['GET'])
def get_workingday(restaurant_id):
    wdays = db.session.query(WorkingDay).filter(WorkingDay.restaurant_id == int(restaurant_id)).all()
    ws = []
    for w in wdays:
        ws.append(wday_to_json(w))
    #print(ws)
    return jsonify(ws)

@api_stub.route('/restaurants/<restaurant_id>/tables')
def get_tables(restaurant_id):
    ts = db.session.query(Table).filter(Table.restaurant_id == int(restaurant_id)).all()
    tables = []
    for t in ts:
        tables.append(table_to_json(t))
    return jsonify(tables)


#get owner by restaurant id
@api_stub.route('/restaurants/<restaurant_id>/owner')
def get_owner(restaurant_id):
    restaurant = db.session.query(Restaurant).filter(Restaurant.id == int(restaurant_id)).first()
    return jsonify(owner=restaurant.owner_id)

#get table name by id
@api_stub.route('/restaurants/<table_id>/table_name')
def get_table(table_id):
    table = db.session.query(Table).filter(Table.id == int(table_id)).first()
    return jsonify(table_name=table.table_name)

#puts a notification for a generic user
@api_stub.route('/users/notification',methods=['GET', 'PUT'])
def notification():
    notif_dict = json.loads(request.json)
    print(str(notif_dict['user_id']))
    user= db.session.query(User).filter(User.id == int(notif_dict['user_id'])).first()
    notification_entry = Notification()
    notification_entry.email = user.email
    notification_entry.date = datetime.datetime.now()
    notification_entry.type_ = Notification.TYPE(int(notif_dict["type"]))
    notification_entry.message = notif_dict["message"]
    notification_entry.user_id = user.id
    db.session.add(notification_entry)
    db.session.commit()
    return "notified"
