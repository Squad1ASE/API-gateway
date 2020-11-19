import requests
from flask import Blueprint, jsonify
from database import db_session, Reservation, Seat
import datetime
import json

import time
from time import mktime
from datetime import timedelta


reservation = Blueprint('reservation', __name__)

# get all the reservation
@reservation.route('/reservation/all', methods=['GET'])
def get_all_reservation():
    reservation_records = db_session.query(Reservation).all()
    #return [reservation.serialize() for reservation in reservation_records]
    return [json.dumps(reservation.serialize()) for reservation in reservation_records]





@reservation.route('/reservation/<int:user_id>/all', methods=['GET'])
def get_reservation_list(user_id):
    user = requests.get('http://127.0.0.1:5000/users/'+str(user_id)) #ASK USERS 
    print('oooooooooooooooooooooooooooo')
    print(user)
    print(user.json())
    #print(user.status_code)
    #print(user.json())
    #print(user.jsonify())
    #user_json = user.jsonify()
    #print(user_json['phone'])

    #user, user_sc = requests.get('http://127.0.0.1:5000/users/'+str(user_id)) #ASK USERS 
    data_dict = []
"""
    if user.json :
    #if user_sc == 200:
        if user['role'] == 'customer':
            reservation_records = db_session.query(Reservation).filter(
                Reservation.booker_id == user['id'],
                Reservation.cancelled == False,
                #Reservation.date >= datetime.datetime.now()
            ).all()

            for reservation in reservation_records:
                restaurant,sc = requests.get("/restaurants/"+reservation.restaurant_id+"/reservation") #ASK RESTAURANTS                       
                if sc == 200:
                    temp_dict = dict(
                        restaurant_name=restaurant['name'],
                        date=reservation.date,
                        reservation_id=reservation.id
                    )
                    data_dict.append(temp_dict)
            return json.dumps(data_dict),200

        elif user['role'] == 'owner':
            restaurants_records, sc = requests.get("/restaurants/"+user['id'])    #ASK RESTAURANTS    
            if sc == 200:
                for restaurant in restaurants_records:
                    reservation_records = db.session.query(Reservation).filter(
                        Reservation.restaurant_id == restaurant['id'],
                        Reservation.cancelled == False,
                        Reservation.date >= datetime.datetime.now() - timedelta(hours=3)
                    ).all()

                    for reservation in reservation_records:
                        seat = db_session.query(Seat).filter(Seat.reservation_id == reservation.id).all()
                        booker, booker_sc = requests.get("/users/"+reservation.booker_id).json() #ASK USERS
                        table, table_sc = requests.get('restaurants/tables'+reservation.table_id) #ASK RESTAURANTS

                        if booker_sc == 200 and table_sc == 200:
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

        elif user['role'] == 'ha': 
            return json.dumps({'message': 'Request not admitted'}),403

        else: 
            reservation_records = db_session.query(Reservation).filter(
                Reservation.booker_id == user['id']
            ).all()
            for reservation in reservation_records:
                temp_dict = dict(
                    reservation_id=reservation.id,
                    booker_id=reservation.booker_id,
                    restaurant_id=reservation.restaurant_id,
                    table_id=reservation.table_id,                    
                    date=reservation.date,
                    cancelled=reservation.cancelled
                )
                data_dict.append(temp_dict)

                seat_records = db_session.query(Seat).filter(Seat.reservation_id == reservation.id).all()
                for seat in seat_records:
                    temp_dict = dict(
                        seat_id=seat.id,
                        restaurant_id=seat.restaurant_id,
                        number_of_guests=len(seat),
                        guests_email=seat.guests_email,
                        confirmed=seat.confirmed                        
                    )
                data_dict.append(temp_dict)
            return json.dumps(data_dict),200

    
    else:
        return json.dumps({'message': 'Failure checking the user'}),401#403

"""