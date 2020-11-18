import json
from flask import Blueprint, jsonify
from database import db_session, Seat, Reservation
import time
import datetime
from time import mktime
from datetime import timedelta

owners = Blueprint('owners', __name__)

@owners.route('/reservation/owners/all', methods=['GET'])
#@login_required
def get_reservation_list():

    #if (current_user.role == 'ha' or current_user.role == 'customer'):
    #    return json.dumps({'message': 'not a owner'}),403

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
                seat = db_session.query(Seat).filter(Seat.reservation_id == reservation.id).all()

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