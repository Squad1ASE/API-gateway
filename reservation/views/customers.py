import requests
from flask import Blueprint, jsonify
from database import db_session, Reservation, Seat
import datetime
import json

customers = Blueprint('customers', __name__)

@customers.route('/reservation/customers/all', methods=['GET'])
#@login_required
def get_reservation_list():
    #if (current_user.role == 'ha' or current_user.role == 'owner'):
    #    return json.dumps({'message': 'not a customer'}),403

    reservation_records = db_session.query(Reservation).filter(
        Reservation.booker_id == 1,
        Reservation.cancelled == False,
        #Reservation.date >= datetime.datetime.now()
    ).all()

    data_dict = []
    for reservation in reservation_records:
        resp,status_code = requests.get("/restaurants/"+reservation.restaurant_id+"/reservation")        
        if(status_code==200):
            temp_dict = dict(
                restaurant_name=resp['name'],
                date=reservation.date,
                reservation_id=reservation.id
            )
            data_dict.append(temp_dict)
    return json.dumps(data_dict),200