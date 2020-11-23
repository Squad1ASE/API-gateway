import requests
from flask import Blueprint, jsonify, Response, request
from reservation.database import db_session, Reservation, Seat
import datetime
import json
import time
from time import mktime
from datetime import timedelta
import connexion
import ast
import reservation.app
#from app.application import delete_restaurant_reservations_task
from reservation.api_call import get_restaurant
import dateutil.parser

reservations = Blueprint('reservation', __name__)

# get all the reservation
def get_all_reservations():
    q = db_session.query(Reservation).filter_by(cancelled=None)
    if 'user_id' in request.args:
        q = q.filter_by(booker_id=request.args['user_id'])
    if 'restaurant_id' in request.args:
        q = q.filter_by(restaurant_id=request.args['restaurant_id'])
    if 'start' in request.args:
        #DATE: 2020-11-22T12:00:00
        start = request.args['start']
        start = dateutil.parser.isoparse(start)
        q = q.filter(Reservation.date >= start)
    if 'end' in request.args:
        end = request.args['end']
        end = dateutil.parser.isoparse(end)
        q = q.filter(Reservation.date <= end)
    return [reservation.serialize() for reservation in q.all()]


# get the reservation with specific id
def get_reservation(reservation_id):
    reservation = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if reservation is None:
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    return reservation.serialize()


# get all the seat for a reservation
def get_seats(reservation_id):
    reservation = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if reservation is None:
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    seats = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    return [seat.serialize() for seat in seats]

# utility to convert days in number
def convert_weekday(day):
    if day == 'monday':
        return 1
    elif day == 'tuesday':
        return 2
    elif day == 'wednesday':
        return 3
    elif day == 'thursday':
        return 4
    elif day == 'friday':
        return 5
    elif day == 'saturday':
        return 6
    elif day == 'sunday':
        return 7

# create a reservation
def create_reservation():

    r = request.json
    print(r)

    date_str = r['date'] + ' ' + r['time']
    date = datetime.datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    restaurant_id = r['restaurant_id']
    
    restaurant = get_restaurant(restaurant_id).json()
    # check if the day is open this day
    weekday = date.weekday() + 1
    workingdays = restaurant['working_days']#get_workingdays(restaurant_id).json()
    workingday = None
    for w in workingdays:
        #TODO: this line if the day is in string format
        if convert_weekday(w['day']) == weekday:
        #if w['day'] == weekday:
            workingday = w
    if workingday is None:
        return connexion.problem(400, 'Error', 'Restaurant is not open this day!')
    
    # check if the restaurant is open this hours
    time_span = False
    reservation_time = time.strptime(r['time'], '%H:%M')
    for shift in workingday['work_shifts']:
        try:
            start = time.strptime(shift[0], '%H:%M')
            end = time.strptime(shift[1], '%H:%M')
            if reservation_time >= start and reservation_time <= end:
                time_span = True
                break
        except Exception as e:
            print(e)

    if time_span is False:
        return connexion.problem(400, 'Error', 'Restaurant is not open at this hour')

    # check if there is any table with this capacity
    all_tables = restaurant['tables']
    tables = []
    for table in all_tables:
        if table['capacity'] >= r['places']:
            tables.append(table)
    if len(tables) == 0:
        return connexion.problem(400, 'Error', 'There are not tables with this capacity!')
    
    # check if there is a table for this amount of time
    start_reservation = date - timedelta(minutes=restaurant['avg_time_of_stay'])
    end_reservation = date + timedelta(minutes=restaurant['avg_time_of_stay'])
    reserved_table_records = db_session.query(Reservation).filter(
            Reservation.date >= start_reservation,
            Reservation.date <= end_reservation,
            Reservation.cancelled == None
        ).all()
    reserved_table_ids = [reservation.table_id for reservation in reserved_table_records]
    tables.sort(key=lambda x: x['capacity'])
    table_id_reservation = None
    for table in tables:
        if table['id'] not in reserved_table_ids:
            table_id_reservation = table['id']
            break
    if table_id_reservation is None:
        return connexion.problem(400, 'Error', "No table available for this amount of people at this time")
    else:
        # add the reservation
        reservation = Reservation()
        reservation.booker_id = r['booker_id']
        reservation.restaurant_id = restaurant_id
        reservation.date = date
        reservation.places = r['places']
        reservation.table_id = table_id_reservation
        db_session.add(reservation)
        db_session.commit()
        seat = Seat()
        seat.confirmed = False
        seat.guests_email = r['booker_email']
        seat.reservation_id = reservation.id
        reservation.seats.append(seat)
        db_session.add(seat)
        db_session.commit()

        return 'Reservation is created succesfully'

def confirm_participants(reservation_id):
    r = request.json
    print(r)
    # get the reservation
    reservation = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if reservation is None:
        #return Response('There is not a reservation with this ID', status=404)
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    if (reservation is None or reservation.date <= datetime.datetime.now() - timedelta(hours=3) or reservation.date >= datetime.datetime.now()):
        return connexion.problem(403, 'Error', 'The reservation is too old or in the future')
    # get the seats
    seats = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    for seat in seats:
        if seat.guests_email in r:
            seat.confirmed = True
        else:
            seat.confirmed = False
    db_session.commit()
    return 'Participants confirmed'



# delete a reservation
def delete_reservation(reservation_id):
    reservation = db_session.query(Reservation).filter(
        Reservation.id == reservation_id,
    ).first()

    if reservation is not None:
        now = datetime.datetime.now()
        if reservation.date < now:
            return connexion.problem(403, 'Error', "You can't delete a past reservation")
        
        restaurant = get_restaurant(restaurant_id).json()

        tables = restaurant['tables']
        table_name = None
        for t in tables:
            if t['id'] == reservation.table_id:
                table_name = t['name']
        #res = requests.get('http://127.0.0.1:5000/restaurants/'+str(reservation.table_id)+'/table_name')
        #table_name = (res.json())['table_name']

        restaurant_owner_id = restaurant['owner_id']
        
        
        reservation.cancelled = 'reservation_deleted'#+' '+str(restaurant_owner_id)+' '+str(table_name)
        db_session.commit()

        return "The reservation is deleted"
    return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')

def delete_reservations():
    if 'restaurant_id' in request.args and 'user_id' in request.args:
        return connexion.problem('400', 'Error', 'Too much query arguments')
    elif 'user_id' in request.args:
        user_id = request.args.get('user_id')
        reservations = db_session.query(Reservation).filter(
            Reservation.booker_id == int(user_id),
        ).all()

        for reservation in reservations:
            reservation.cancelled = 'user_deleted'
            db_session.commit()
        return "User reservations deleted"
    elif 'restaurant_id' in request.arg:
        restaurant_id = request.args.get('restaurant_id')
        restaurant_name = get_restaurant_name(restaurant_id).json()

        reservations = db_session.query(Reservation).filter(
            Reservation.restaurant_id == int(restaurant_id),
        ).all()

        for reservation in reservations:
            reservation.cancelled='restaurant_deleted'+' '+str(restaurant_name)
            db_session.commit()

        return "Restaurant reservations deleted"
    else:
        return connexion.problem('400', 'Error', 'You must specify an ID')

    


#edit the reservation with specific id
def edit_reservation(reservation_id):

    old_res = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if old_res is None:
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')    

    r = request.json # save all new seats data and places if changed
    print(r)

    if r['places'] <= 0:
        print(r['places'])
        return connexion.problem(400, 'Error', 'You cannot book for less people than your self!')

        
    if r['places'] != old_res.places: # change table_id only if places changed        
  
        restaurant = get_restaurant(old_res.restaurant_id).json()
        avg_time_of_stay = restaurant['avg_time_of_stay']
        all_tables = restaurant['tables']
        tables = []
        found = False
        for table in all_tables:
            if table['capacity'] > r['places']:
                if table['id'] == old_res.table_id:
                    found = True
                    break
                else:
                    tables.append(table)

        if len(tables) == 0 and found == False:
            print(tables)
            return connexion.problem(400, 'Error', 'There are not tables with this capacity!')

        elif found == False: 
            date = old_res.date
            # check if there is a table for this amount of time
            start_reservation = date - timedelta(minutes=avg_time_of_stay)
            end_reservation = date + timedelta(minutes=avg_time_of_stay)         
            reserved_table_records = db_session.query(Reservation).filter(
                    Reservation.date >= start_reservation,
                    Reservation.date <= end_reservation,
                    Reservation.cancelled == None
                ).all()
            reserved_table_ids = [reservation.table_id for reservation in reserved_table_records]
            tables.sort(key=lambda x: x['capacity'])
            table_id_reservation = None
            for table in tables:
                if table['id'] not in reserved_table_ids:
                    table_id_reservation = table['id']
                    break
            if table_id_reservation is None:
                print(table_id_reservation)
                return connexion.problem(400, 'Error', "No table available for this amount of people at this time")

            else:
                old_res.table_id = table_id_reservation
                db_session.commit()

        old_res.places = r['places']    
        db_session.commit()
    # change seats_emails --> remove all the olds and save the news (without booker_email)

    old_seats = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    for s in old_seats:
        print(s.guests_email, r['booker_email'])
        if s.guests_email != r['booker_email']:

            db_session.delete(s)
            db_session.commit()


    for s in r['seats_email']: #get an array of new seats
        print(s)
        #print(i['confirmed'])
        if s['guest_email'] != r['booker_email']:

            seat = Seat()
            seat.reservation_id = old_res.id  
            seat.guests_email = s['guest_email']
            seat.confirmed = False

            old_res.seats.append(seat)
            db_session.add(seat)
            db_session.commit()

    return 'Reservation is edited successfully'
