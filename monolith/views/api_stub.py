from flask import Blueprint, redirect, render_template, request, make_response, jsonify
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




