import requests
from flask import Blueprint, jsonify, Response, request
from database import db_session, Reservation, Seat
import datetime
import json
import time
from time import mktime
from datetime import timedelta
#from app import delete_reservations_task
import connexion

reservation = Blueprint('reservation', __name__)


# get all the reservation
def get_all_reservation():
    reservation_records = db_session.query(Reservation).all()
    return [reservation.serialize() for reservation in reservation_records]


# get the reservation with specific id
def get_reservation(reservation_id):
    reservation = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if reservation is None:
        # return Response('There is not a reservation with this ID', status=404)
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    return reservation.serialize()


# get all the seat for a reservation
def get_seats(reservation_id):
    reservation = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if reservation is None:
        # return Response('There is not a reservation with this ID', status=404)
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    seats = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    return [seat.serialize() for seat in seats]


# get all the reservations for a restaurant
def get_restaurant_reservations(restaurant_id):
    # get the future reservation
    reservation_records = db.session.query(Reservation).filter(Reservation.restaurant_id == restaurant_id,
                                                               Reservation.cancelled == False,
                                                               Reservation.date >= datetime.datetime.now() - timedelta(
                                                                   hours=3)).all()
    return [reservation.serialize() for reservation in reservation_records]


# create a reservation
def create_reservation(user_id):
    r = request.json
    # print(r)
    reservation = Reservation()
    reservation.booker_id = r['booker_id']
    reservation.restaurant_id = r['restaurant_id']
    reservation.date = r['date']
    seats = []
    for seat in r['seats']:
        seats.append(seat)
    reservation.seat = seats
    db_session.add(reservation)
    db_session.commit()
    return 'Reservation is created succesfully'


# delete a reservation
def delete_reservation(reservation_id):
    reservation = db_session.query(Reservation).filter(
        Reservation.id == reservation_id,
    ).first()

    if reservation is not None:
        now = datetime.datetime.now()
        if reservation.date < now:
            return connexion.problem(403, 'Error', "You can't delete a past reservation")

        # todo chiamare task celery
        # delete_reservations_task([reservation_id]).delay()
        reservation.cancelled == True
        db_session.commit()

        seat_query = Seat.query.filter_by(reservation_id=reservation.id).all()

        for seat in seat_query:
            seat.confirmed = False


        table_name = requests.get('http://127.0.0.1:5000/restaurants/' + str(reservation.restaurant_id) + '/' + str(
            reservation.table_id)).json()['table_name']

        restaurant_owner_id = int(requests.get(
            'http://127.0.0.1:5000/restaurants/' + str(reservation.restaurant_id) + '/owner').json()['owner'])

        notification = jsonify(
            date=now,
            type=2,
            message='The reservation of the ' + table_name + ' table for the date ' + str(
                reservation.date) + ' has been canceled',
            user_id=restaurant_owner_id
        )

        requests.put('http://127.0.0.1:5000/users/notification', json=notification)
        return "The reservation is deleted"
    return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')


# get all the reservation in which user is interested
def get_user_reservations(user_id):
    reservation_records = db_session.query(Reservation).filter_by(booker_id=user_id).all()
    return [reservation.serialize() for reservation in reservation_records]
    '''
    user = requests.get('http://127.0.0.1:5000/users/'+str(user_id)) #ASK USERS 
    #print(user.status_code)

    data_dict = []
    if user.status_code == 200 :
        user_content = user.json()
        #print(user_content['phone'])
        print(user_content['role'])

        if user_content['role'] == 'customer':  #TODO complete first post reservation in our db
            reservation_records = db_session.query(Reservation).filter(
                Reservation.booker_id == user_content['id'],
                Reservation.cancelled == False,
                #Reservation.date >= datetime.datetime.now()
            ).all()
            #print(len(reservation_records))

            for reservation in reservation_records:

                restaurant = requests.get("http://127.0.0.1:5000/restaurants/reservation/"+str(reservation.restaurant_id)) #ASK RESTAURANTS                       
                if restaurant.status_code == 200:
                    restaurant_content = restaurant.json()

                    temp_dict = dict(
                        restaurant_name=restaurant_content['name'],
                        date=reservation.date,
                        reservation_id=reservation.id
                    )
                    data_dict.append(temp_dict)
            return data_dict

        elif user_content['role'] == 'owner':
            restaurants_records = requests.get("http://127.0.0.1:5000/restaurants/users/"+str(user_content['id']))    #ASK RESTAURANTS    
            if restaurant_records.status_code == 200:
                restaurant_records_content = restaurant_records.json()

                for restaurant in restaurants_records_content:
                    reservation_records = db.session.query(Reservation).filter(
                        Reservation.restaurant_id == restaurant['id'],
                        Reservation.cancelled == False,
                        Reservation.date >= datetime.datetime.now() - timedelta(hours=3)
                    ).all()

                    for reservation in reservation_records:
                        seat = db_session.query(Seat).filter(Seat.reservation_id == reservation.id).all()
                        booker = requests.get("http://127.0.0.1:5000/users/"+str(reservation.booker_id)) 
                        table = requests.get('http://127.0.0.1:5000/restaurants/tables'+str(reservation.table_id)) #ASK RESTAURANTS

                        if booker.status_code == 200 and table.status_code == 200:
                            booker_content = booker.json()
                            table_content = table.json()

                            temp_dict = dict(
                                restaurant_name=restaurant['name'],
                                restaurant_id=restaurant['id'],
                                date=reservation.date,
                                table_name=table_content['table_name'],
                                booker_fn=booker_content['firstname'],
                                booker_ln=booker_content['lastname'],
                                booker_phone=booker_content['phone'],
                                reservation_id=reservation.id
                            )
                            data_dict.append(temp_dict)
                data_dict = sorted(data_dict, key=lambda i: (i['restaurant_name'], i['date']))
            return data_dict

        elif user_content['role'] == 'ha': 
            return  Response('It is not allowed', status=403)

        else: 
            reservation_records = db_session.query(Reservation).filter(
                Reservation.booker_id == user_content['id']
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
                        reservation_id=seat.reservation_id,
                        guests_email=seat.guests_email,
                        confirmed=seat.confirmed                        
                    )
                data_dict.append(temp_dict)
            return data_dict
    else:
        return Response('It is not a user', status=403)
    '''
