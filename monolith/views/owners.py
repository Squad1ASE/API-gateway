import json

from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, User, Review, Restaurant, Like, WorkingDay, Table, Dish, Seat, Reservation, \
    Quarantine, Notification
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import (DishForm, UserForm, RestaurantForm, ReservationPeopleEmail,
                            SubReservationPeopleEmail, ReservationRequest, RestaurantSearch,
                            EditRestaurantForm, ReviewForm)
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

owners = Blueprint('owners', __name__)


@owners.route('/reservation/owners/all', methods=['GET'])
@login_required
def get_reservation_list():

    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return json.dumps({'message': 'not a owner'}),403

    data_dict = []

    #restaurants_records = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    restaurants_records,status_code = requests.get("/restaurants/"+current_user.id)    #ASK FOR THIS ENDPOINT    

    if status_code==200:

        for restaurant in restaurants_records:

            reservation_records = db.session.query(Reservation).filter(
                Reservation.restaurant_id == restaurant['id'],
                Reservation.cancelled == False,
                Reservation.date >= datetime.datetime.now() - timedelta(hours=3)
            ).all()

            for reservation in reservation_records:
                seat = db.session.query(Seat).filter(Seat.reservation_id == reservation.id).all()

                #booker = db.session.query(User).filter(User.id == reservation.booker_id).first()
                booker, booker_statuc_code = requests.get("/users/"+reservation.booker_id).first() #ASK FOR THIS ENDPOINT  

                #table = db.session.query(Table).filter(Table.id == reservation.table_id).first()
                table, table_status_code = requests.get('restaurants/tables'+reservation.table_id).first() #ASK FOR THIS ENDPOINT

                if booker_status_code == 200 and table_status_code == 200:
                    temp_dict = dict(
                        restaurant_name=restaurant['name'],
                        restaurant_id=restaurant['id'],
                        date=reservation.date,
                        table_name=table['table_name'],
                        number_of_guests=len(seat),
                        booker_fn=booker['firstname'],
                        booker_ln=booker['lastname'],
                        booker_phone=booker['phone'],
                        reservation_id=reservation.id
                    )
                    data_dict.append(temp_dict)

        data_dict = sorted(data_dict, key=lambda i: (i['restaurant_name'], i['date']))

    return json.dumps(data_dict),200



    """
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page",
                                                 redirect_url="/"), 403)

        data_dict = []
        restaurants_records = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()

        for restaurant in restaurants_records:

            reservation_records = db.session.query(Reservation).filter(
                Reservation.restaurant_id == restaurant.id,
                Reservation.cancelled == False,
                Reservation.date >= datetime.datetime.now() - timedelta(hours=3)
            ).all()

            for reservation in reservation_records:
                booker = db.session.query(User).filter(User.id == reservation.booker_id).first()
                seat = db.session.query(Seat).filter(Seat.reservation_id == reservation.id).all()
                table = db.session.query(Table).filter(Table.id == reservation.table_id).first()
                temp_dict = dict(
                    restaurant_name=restaurant.name,
                    restaurant_id=restaurant.id,
                    date=reservation.date,
                    table_name=table.table_name,
                    number_of_guests=len(seat),
                    booker_fn=booker.firstname,
                    booker_ln=booker.lastname,
                    booker_phone=booker.phone,
                    reservation_id=reservation.id
                )
                data_dict.append(temp_dict)

        data_dict = sorted(data_dict, key=lambda i: (i['restaurant_name'], i['date']))

    return render_template('restaurant_reservations_list.html', reservations=data_dict)
    """