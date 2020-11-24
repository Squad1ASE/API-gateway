
from reservation.tests.conftest import test_app

from reservation.database import db_session, Reservation, Seat
from sqlalchemy import exc
from unittest import mock
from unittest.mock import patch
import datetime

from reservation.views.reservation import (get_restaurant, get_restaurant_name, create_reservation, edit_reservation,
                                            confirm_participants, delete_reservation, delete_reservations, put_notification)
from reservation.app import delete_reservations_task, hello
from reservation.utilities import (edit_reservation_EP, restaurant_example, confirm_participants_EP, participants_example,
                                        reservation_example, tables_example, restaurant_reservations_EP, 
                                        user_reservations_EP, create_reservation_EP, edit_reservation_example,
                                        delete_reservation_EP, restaurant_h24_example, reservation_future_example, 
                                        reservation_now_example, edit_reservation_future_example, reservation_yesterday_example,
                                        edit_ERROR_reservation_future_example, edit_ERROR2_reservation_future_example,
                                        edit_ERROR3_reservation_future_example, delete_all_reservations_EP,
                                        delete_user_reservations_example, delete_restaurant_reservations_example,
                                        get_reservation_EP, get_reservations_EP, create_ERROR_reservation_example, 
                                        create_ERROR2_reservation_example, create_ERROR3_reservation_example,
                                        create_reservation_example, create_ERROR4_reservation_example,
                                        delete_USER_reservations_example, edit_ERROR1_reservation_future_example,
                                        contact_tracing_EP, contact_tracing_example, restaurant_closed_h24_example, 
                                        reservation_example_closed_restaurant, edit_ERROR4_reservation_closed_restaurant_example,
                                        delete_ERROR_reservations_example, delete_RESTAURANT_reservations_example)


# command : pytest tests -s --cov=reservation --cov-report term-missing

@patch('reservation.views.reservation.get_restaurant')
def test_unit_reservations(mock1, test_app):
    app, test_client = test_app

    #-------------------------------------------------------------------------------CREATE
    # creation of a reservation without a restaurant example
    with app.test_request_context(json=reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is None

    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_example
    mock1.return_value = ok_mock

    # creation of a reservation in a not working day
    with app.test_request_context(json=create_ERROR_reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is None

    # creation of a reservation in a not working time
    with app.test_request_context(json=create_ERROR2_reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is None

    # creation of a reservation but there are not tables with this capacity
    with app.test_request_context(json=create_ERROR3_reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is None

    # creation of a reservation and occupy all the tables
    with app.test_request_context(json=create_reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == create_reservation_example['restaurant_id'] #1
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == create_reservation_example['places']
    assert reservation.cancelled is None

    # creation of new reservation but there are no more tables
    with app.test_request_context(json=create_ERROR4_reservation_example):
        assert create_reservation()
    again_reservation = db_session.query(Reservation).filter_by(id=2).first()
    assert again_reservation is None

    db_session.delete(reservation)
    db_session.commit()

    #--------------------------------------------------------------------------------------EDIT
    
    tables = tables_example    
    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock

    # edit a reservation that is not present    
    with app.test_request_context(json=edit_reservation_example):
        assert edit_reservation(1) #connexion:404


    # creation of a reservation in the past
    with app.test_request_context(json=reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == reservation_example['restaurant_id']
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == reservation_example['places']
    assert reservation.cancelled is None

    # no changes, since the reservation is of the past
    with app.test_request_context(json=edit_reservation_example):
        assert edit_reservation(reservation.id)
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == reservation_example['restaurant_id']
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == 2

    # ok changes, since the reservation is in the future
    with app.test_request_context(json=reservation_future_example):
        assert create_reservation()
    unchanged_reservation = db_session.query(Reservation).filter_by(id=2).first()
    assert unchanged_reservation.places == reservation_future_example['places']
    assert unchanged_reservation.booker_id == reservation_future_example['booker_id']
    unchanged_seat_res_owner = db_session.query(Seat).filter_by(reservation_id=2).all()    
    assert len(unchanged_seat_res_owner) == 1
    for s in unchanged_seat_res_owner:
        assert s.guests_email == reservation_future_example['booker_email']

    with app.test_request_context(json=edit_reservation_future_example):
        assert edit_reservation(2)
    changed_reservation = db_session.query(Reservation).filter_by(id=2).first()
    assert changed_reservation is not None    
    assert changed_reservation.places == edit_reservation_future_example['places']
    changed_seat = db_session.query(Seat).filter_by(reservation_id=2).all()
    assert len(changed_seat) <= changed_reservation.places
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='userexample1@test.com').first() != None
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='test@test.com').first() != None
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='test2@test.com').first() != None

    # error with date of the past
    with app.test_request_context(json=edit_ERROR_reservation_future_example):
        assert edit_reservation(2)

    # error because places is not >= 1
    with app.test_request_context(json=edit_ERROR1_reservation_future_example):
        assert edit_reservation(2)

    #error because there are no tables
    with app.test_request_context(json=edit_ERROR2_reservation_future_example):
        assert edit_reservation(2)

    # error because number of emails > number of places
    with app.test_request_context(json=edit_ERROR3_reservation_future_example):
        assert edit_reservation(2)


    # error in a reservation of a not working day   TODO does not enter in the cases of a not working day
    with app.test_request_context(json=reservation_example_closed_restaurant):
        assert create_reservation()
    reservation = db_session.query(Reservation).filter_by(id=3).first()
    assert reservation != None
    with app.test_request_context(json=edit_ERROR4_reservation_closed_restaurant_example):
        assert edit_reservation(reservation.id)



    # TODO here does not go in connexion problem______________________________________
    wrong_mock = mock.MagicMock()
    type(wrong_mock).status_code = mock.PropertyMock(return_value=500)
    wrong_mock.json.return_value = restaurant_h24_example
    mock1.return_value = wrong_mock

    with app.test_request_context(json=edit_reservation_future_example):
        assert edit_reservation(2)

    # for the testing of wrong working day and wrong time see the tests for the creation
    #________________________________________________________________________________________




    
    #-------------------------------------------------------------------------------PARTICIPANTS

    # confirm participants of a not existing reservation
    with app.test_request_context():
        assert confirm_participants(100)

    # confirm participants of a too old reservation
    with app.test_request_context():
        assert confirm_participants(1)

    #-------------------------------------------------------------------------------DELETE

    # delete a reservation of the past
    with app.test_request_context():
        assert delete_reservation(1)

    # delete a reservation that does not exist
    with app.test_request_context():
        assert delete_reservation(100)

    # delete a reservation of the future but restaurant is not available ------------------------------
    wrong_mock = mock.MagicMock()
    type(wrong_mock).status_code = mock.PropertyMock(return_value=500)
    wrong_mock.json.return_value = restaurant_h24_example
    mock1.return_value = wrong_mock

    with app.test_request_context():
        assert delete_reservation(2)
    reservations = db_session.query(Reservation).all()
    assert reservations != None


    #---------------------------------------------------------------------------------------------------
    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock

    with app.test_request_context(json=delete_ERROR_reservations_example):
        assert delete_reservations()
    reservations = db_session.query(Reservation).all()
    assert reservations != None

    wrong_mock = mock.MagicMock()
    type(wrong_mock).status_code = mock.PropertyMock(return_value=500)
    wrong_mock.json.return_value = restaurant_h24_example
    mock1.return_value = wrong_mock

    with app.test_request_context(json=delete_USER_reservations_example):
        assert delete_reservations()

    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock

    with app.test_request_context(json=delete_USER_reservations_example):
        assert delete_reservations()

    wrong_mock = mock.MagicMock()
    type(wrong_mock).status_code = mock.PropertyMock(return_value=500)
    wrong_mock.json.return_value = restaurant_h24_example
    mock1.return_value = wrong_mock

    #with app.test_request_context(json=delete_RESTAURANT_reservations_example):
    #    assert delete_reservations()

    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock

    #with app.test_request_context(json=delete_RESTAURANT_reservations_example):
    #    assert delete_reservations()


@patch('reservation.views.reservation.get_restaurant')
def test_component_reservations(mock1, test_app):

    tables = tables_example
    ok_mock = mock.MagicMock()
    type(ok_mock).status_code = mock.PropertyMock(return_value=200)
    ok_mock.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock
    
    app, test_client = test_app

    # no changes, since the reservation does not exist
    assert edit_reservation_EP(test_client, 1, edit_reservation_example).status_code == 404

    # create reservation now
    assert create_reservation_EP(test_client, reservation_now_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_now_example['booker_id']).first()
    assert restaurant_reservations_EP(test_client, res.id).status_code == 200
    assert user_reservations_EP(test_client, res.id).status_code == 200
    seat = Seat()
    seat.reservation_id = res.id  
    seat.guests_email = 'test@test.com'
    seat.confirmed = False
    res.seats.append(seat)
    seat2 = Seat()
    seat2.reservation_id = res.id  
    seat2.guests_email = 'test2@test.com'
    seat2.confirmed = False
    res.seats.append(seat2)
    db_session.commit()
    # confirm participants
    assert confirm_participants_EP(test_client, res.id, participants_example).status_code == 200
    assert get_reservation_EP(test_client, res.id).status_code == 200
    assert get_reservations_EP(test_client, '').status_code == 200
    assert get_reservations_EP(test_client, '?restaurant_id=2&start=2012-12-31T22:00:00.000Z&end=2012-12-31T22:00:00.000Z').status_code == 200
    db_session.delete(res)
    db_session.commit()

    # create a reservation in the past
    assert create_reservation_EP(test_client, reservation_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_example['booker_id']).first()
    #error in editing a past reservation
    assert edit_reservation_EP(test_client, res.id, edit_reservation_example).status_code == 400 
    db_session.delete(res)
    db_session.commit()


    # create reservation in the future
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_future_example['booker_id']).first()

    # edit reservation in the future
    assert edit_reservation_EP(test_client, res.id, edit_reservation_future_example).status_code == 200 

    # error in editing a reservation with a number of places <1
    assert edit_reservation_EP(test_client, res.id, edit_ERROR_reservation_future_example).status_code == 400 

    # error in editing a reservation with a number of places > all table capacities
    assert edit_reservation_EP(test_client, res.id, edit_ERROR2_reservation_future_example).status_code == 400 
    
    # error in editing a reservation with a number of emails > places
    assert edit_reservation_EP(test_client, res.id, edit_ERROR3_reservation_future_example).status_code == 400 

    db_session.delete(res)
    db_session.commit()
    

@patch('reservation.views.reservation.get_restaurant')
@patch('reservation.views.reservation.get_restaurant_name')
def test_component_delete(mock1, mock2, test_app):
    ok_mock2 = mock.MagicMock()
    ok_mock1 = mock.MagicMock()
    type(ok_mock2).status_code = mock.PropertyMock(return_value=200)
    ok_mock2.json.return_value = restaurant_h24_example['name']
    mock2.return_value = ok_mock1
    ok_mock = mock.MagicMock()
    type(ok_mock1).status_code = mock.PropertyMock(return_value=200)
    ok_mock1.json.return_value = restaurant_h24_example
    mock1.return_value = ok_mock2
    app, test_client = test_app
    # delete the reservation
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_future_example['booker_id']).first()
    assert delete_reservation_EP(test_client, res.id).status_code == 200
    db_session.delete(res)
    db_session.commit()
    # recreate the reservation
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    assert get_reservations_EP(test_client, '?user_id='+str(reservation_future_example['booker_id'])).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_future_example['booker_id']).first()
    # delete the reservations of the user
    assert delete_all_reservations_EP(test_client, delete_user_reservations_example).status_code == 200
    assert get_reservation_EP(test_client, res.id).status_code == 404
    db_session.delete(res)
    db_session.commit()
    # recreate the reservation
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_future_example['booker_id']).first()
    # delete the reservations of the restaurant
    assert delete_all_reservations_EP(test_client, delete_restaurant_reservations_example).status_code == 200

@patch('reservation.views.reservation.get_restaurant')
@patch('reservation.views.reservation.put_notification')
def test_contact_tracing(mock1, mock2, test_app):
    app, test_client = test_app
    ok_mock1 = mock.MagicMock()
    type(ok_mock1).status_code = mock.PropertyMock(return_value=200)
    mock1.return_value = ok_mock1
    ok_mock2 = mock.MagicMock()
    type(ok_mock2).status_code = mock.PropertyMock(return_value=200)
    ok_mock2.json.return_value = restaurant_h24_example
    mock2.return_value = ok_mock2
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    assert create_reservation_EP(test_client, reservation_yesterday_example).status_code == 200
    res = db_session.query(Reservation).filter_by(booker_id = reservation_yesterday_example['booker_id']).first()
    # add a participants and send notification to it and to owner of the restaurant
    res.seats[0].confirmed = True
    seat = Seat()
    seat.reservation_id = res.id  
    seat.guests_email = 'test@test.com'
    seat.confirmed = True
    res.seats.append(seat)
    db_session.commit()
    assert contact_tracing_EP(test_client, contact_tracing_example).status_code == 200

@patch('reservation.app.put_notification')
def test_task_celery(mock1, test_app):
    app, test_client = test_app
    hello()
    ok_mock1 = mock.MagicMock()
    fail_mock1 = mock.MagicMock()
    type(fail_mock1).status_code = mock.PropertyMock(return_value=500)
    type(ok_mock1).status_code = mock.PropertyMock(return_value=200)
    mock1.return_value = fail_mock1
    reservation = Reservation()
    reservation.booker_id = 1
    reservation.restaurant_id = 1
    reservation.date = datetime.datetime.now()#.strptime('%d/%m/%Y %H:%M')
    reservation.places = 2
    reservation.table_id = 1
    reservation.cancelled = 'reservation_deleted'+' '+str(1)+' '+str('yellow')
    db_session.add(reservation)
    db_session.commit()
    reservation = Reservation()
    reservation.booker_id = 2
    reservation.restaurant_id = 1
    reservation.date = datetime.datetime.now()#.strptime('%d/%m/%Y %H:%M')
    reservation.places = 2
    reservation.table_id = 1
    reservation.cancelled = 'user_deleted' +' '+str(1)+' '+str('yellow')
    db_session.add(reservation)
    db_session.commit()
    reservation = Reservation()
    reservation.booker_id = 3
    reservation.restaurant_id = 1
    reservation.date = datetime.datetime.now()#.strptime('%d/%m/%Y %H:%M')
    reservation.places = 2
    reservation.table_id = 1
    reservation.cancelled = 'restaurant_deleted'+' '+str('restaurant_name')
    db_session.add(reservation)
    db_session.commit()
    # fail case
    delete_reservations_task()
    # ok case
    mock1.return_value = ok_mock1
    delete_reservations_task()
    res = db_session.query(Reservation).filter_by(booker_id=1).first()
    assert res is None
    res = db_session.query(Reservation).filter_by(booker_id=2).first()
    assert res is None
    res = db_session.query(Reservation).filter_by(booker_id=3).first()
    assert res is None


