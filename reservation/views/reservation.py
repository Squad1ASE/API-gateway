import requests
from flask import Blueprint, jsonify
from database import db_session, Reservation, Seat
import datetime
import json

reservation = Blueprint('reservation', __name__)

# get all the reservation
@reservation.route('/reservation/all', methods=['GET'])
def get_all_reservation():

    reservation_records = db_session.query(Reservation).all()
    return [reservation.serialize() for reservation in reservation_records]