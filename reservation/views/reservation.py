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
import ast

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
    reservation_records = db_session.query(Reservation).filter(Reservation.restaurant_id == restaurant_id, Reservation.cancelled == False, Reservation.date >= datetime.datetime.now() - timedelta(hours=3)).all()
    return [reservation.serialize() for reservation in reservation_records]


# create a reservation
def create_reservation(user_id):

    r = request.json

    date_str = r['date'] + ' ' + r['time']
    date = datetime.datetime.strptime(date_str, "%d/%m/%Y %H:%M")
    restaurant_id = r['restaurant_id']
    
    #restaurant = requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id))
    # check if the day is open this day
    weekday = date.weekday() + 1
    workingdays = requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/workingdays').json()
    #print(workingdays)
    workingday = None
    for w in workingdays:
        wd = ast.literal_eval(w)
        print(wd)
        if wd['day'] == weekday:
            workingday = wd
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
    all_tables = requests.get('http://127.0.0.1:5000/restaurants/'+str(restaurant_id)+'/tables').json()
    tables = []
    for table in all_tables:
        t = ast.literal_eval(table)
        print(t)
        if t['capacity'] >= r['places']:
            tables.append(t)
    if len(tables) == 0:
        return connexion.problem(400, 'Error', 'There are not tables with this capacity!')
    
    # check if there is a table for this amount of time
    #TODO: make it with the right amount of time
    start_reservation = date - timedelta(minutes=15)#restaurant.avg_time_of_stay)
    end_reservation = date + timedelta(minutes=15)#restaurant.avg_time_of_stay)
    reserved_table_records = db_session.query(Reservation).filter(
            Reservation.date >= start_reservation,
            Reservation.date <= end_reservation,
            Reservation.cancelled == False
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

        # todo chiamare task celery
        # delete_reservations_task([reservation_id]).delay()
        reservation.cancelled = True
        db_session.commit()

        seat_query = db_session.query(Seat).filter_by(reservation_id=reservation.id).all()

        for seat in seat_query:
            seat.confirmed = False
        db_session.commit()
        res = requests.get('http://127.0.0.1:5000/restaurants/'+str(reservation.table_id)+'/table_name')
        table_name = (res.json())['table_name']

        restaurant_owner_id = int((requests.get(
            'http://127.0.0.1:5000/restaurants/' + str(reservation.restaurant_id) + '/owner').json())['owner'])

        notification = {
            "type":2,
            "message":'The reservation of the ' + table_name + ' table for the date ' + str(
                reservation.date) + ' has been canceled',
            "user_id":restaurant_owner_id
        }

        requests.put('http://127.0.0.1:5000/users/notification', json=json.dumps(notification))
        return "The reservation is deleted"
    return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')

#edit the reservation with specific id
def edit_reservation(reservation_id):
    """
    # without number of places changed
    old_res = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if old_res is None:
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')

    #db_session.delete(old_res.seats) # delete all old seats data DOES NOT WORK IN THIS WAY
    
    seats_to_remove = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    for s in seats_to_remove:
        db_session.delete(s)

    rs = request.json # save all new seats data

    for r in rs: #get an array of new seats
        #print(i['confirmed'])

        seat = Seat()
        seat.reservation_id = reservation_id
        seat.guests_email = r['guests_email']
        seat.confirmed = r['confirmed']
        db_session.add(seat)

    db_session.commit()        
    return 'Reservation is edited successfully'

    """

    # {'places':2}
    # {'seats': [{-----}]}
    #curl -i -d "{'places':2, 'seats':[{'confirmed':false,'guests_email':'testONE@test.com','id':33,'reservation_id':1}]}" http://127.0.0.1:5000/reservations/1


    old_res = db_session.query(Reservation).filter_by(id=reservation_id).first()
    if old_res is None:
        return connexion.problem(404, 'Not found', 'There is not a reservation with this ID')
    

    r = request.json # save all new seats data and places if changed

    all_tables = requests.get('http://127.0.0.1:5000/restaurants/'+str(old_res.restaurant_id)+'/tables').json()    
    tables = []
    changed = True
    for table in all_tables:        
        t = ast.literal_eval(table)
        print(t)
        if t['id'] == old_res.table_id and t['capacity'] == r['places']: #no table changes
            changed = False       
        if t['capacity'] > r['places']:
            tables.append(t)
    if changed:
        if len(tables) == 0:
            return connexion.problem(400, 'Error', 'There are not tables with this capacity!')
        else: # assign new table
            old_res.places = r['places']
            old_res.table_id = None

            #date_str = old_res.date
            #date = datetime.datetime.strptime(date_str, "%d/%m/%Y %H:%M")
            date = old_res.date
            # check if there is a table for this amount of time
            #TODO: make it with the right amount of time
            start_reservation = date - timedelta(minutes=15)#restaurant.avg_time_of_stay)
            end_reservation = date + timedelta(minutes=15)#restaurant.avg_time_of_stay)            
            reserved_table_records = db_session.query(Reservation).filter(
                    Reservation.date >= start_reservation,
                    Reservation.date <= end_reservation,
                    Reservation.cancelled == False
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
                old_res.table_id = table_id_reservation

    # case changed=False or len(tables)>0 change seat

    old_seats = db_session.query(Seat).filter_by(reservation_id=reservation_id).all()
    for s in old_seats:
        db_session.delete(s)


    for s in r['seats']: #get an array of new seats
        #print(i['confirmed'])

        seat = Seat()
        seat.reservation_id = old_res.id  #s['reservation_id']
        seat.guests_email = s['guests_email']
        seat.confirmed = s['confirmed']

        old_res.seats.append(seat)
        db_session.add(seat)
        

    db_session.commit()        
    return 'Reservation is edited successfully'






# get all the reservation in which user is interested
def get_user_reservations(user_id):
    reservation_records = db_session.query(Reservation).filter_by(booker_id=user_id,cancelled=False).all()
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
