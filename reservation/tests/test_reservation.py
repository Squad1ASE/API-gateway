
from reservation.tests.conftest import test_app

from reservation.database import db_session, Reservation, Seat
from sqlalchemy import exc
from unittest import mock
from unittest.mock import patch
import datetime

from reservation.views.reservation import get_restaurant, create_reservation, edit_reservation
from reservation.utilities import (edit_reservation_EP, restaurant_example, confirm_participants_EP, participants_example,
                                        reservation_example, tables_example, restaurant_reservations_EP, 
                                        user_reservations_EP, create_reservation_EP, edit_reservation_example,
                                        delete_reservation_EP, restaurant_h24_example, reservation_future_example, 
                                        reservation_now_example, edit_reservation_future_example,
                                        edit_ERROR_reservation_future_example, edit_ERROR2_reservation_future_example,
                                        edit_ERROR3_reservation_future_example)

@patch('reservation.views.reservation.get_restaurant')
def test_unit_reservations(mock1, test_app):
    tables = tables_example
    
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = restaurant_h24_example
    #mock2.return_value.status_code.return_value = 200
    #mock2.return_value.json.return_value = tables

    app, test_client = test_app

    # creation of a reservation
    with app.test_request_context(json=reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == 1
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == 2

    # no changes, since the reservation is of the past
    with app.test_request_context(json=edit_reservation_example):
        assert edit_reservation(reservation.id)
    reservation = db_session.query(Reservation).filter_by(id=1).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == 1
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == 2

    # ok changes, since the reservation is in the future
    with app.test_request_context(json=reservation_future_example):
        assert create_reservation()
    unchanged_reservation = db_session.query(Reservation).filter_by(id=2).first()
    assert unchanged_reservation.places == 2
    assert unchanged_reservation.booker_id == 2
    unchanged_seat_res_owner = db_session.query(Seat).filter_by(reservation_id=2).all()    
    assert len(unchanged_seat_res_owner) == 1
    for s in unchanged_seat_res_owner:
        assert s.guests_email == 'userexample1@test.com'

    with app.test_request_context(json=edit_reservation_future_example):
        assert edit_reservation(unchanged_reservation.id)
    changed_reservation = db_session.query(Reservation).filter_by(id=2).first()
    assert changed_reservation is not None    
    assert changed_reservation.places == 3
    changed_seat = db_session.query(Seat).filter_by(reservation_id=2).all()
    assert len(changed_seat) <= changed_reservation.places
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='userexample1@test.com').first() != None
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='test@test.com').first() != None
    assert db_session.query(Seat).filter_by(reservation_id=2, guests_email='test2@test.com').first() != None



@patch('reservation.views.reservation.get_restaurant')
def test_component_reservations(mock1, test_app):
    tables = tables_example
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = restaurant_h24_example
    
    app, test_client = test_app

    # no changes, since the reservation does not exist
    assert edit_reservation_EP(test_client, 1, edit_reservation_example).status_code == 404 

    # create reservation in the past
    assert create_reservation_EP(test_client, reservation_now_example).status_code == 200
    assert restaurant_reservations_EP(test_client, 1).status_code == 200
    assert user_reservations_EP(test_client, 1).status_code == 200


    # add guests email via edit

    #error in editing a past reservation
    assert edit_reservation_EP(test_client, 1, edit_reservation_example).status_code == 400 

    # create reservation in the future
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200

    # edit reservation in the future
    assert edit_reservation_EP(test_client, 2, edit_reservation_future_example).status_code == 200 

    # error in editing a reservation with a number of places <1
    assert edit_reservation_EP(test_client, 2, edit_ERROR_reservation_future_example).status_code == 400 

    # error in editing a reservation with a number of places > all table capacities
    assert edit_reservation_EP(test_client, 2, edit_ERROR2_reservation_future_example).status_code == 400 
    
    # error in editing a reservation with a number of emails > places
    assert edit_reservation_EP(test_client, 2, edit_ERROR3_reservation_future_example).status_code == 400 



    # confirm participants
    assert confirm_participants_EP(test_client, 1, participants_example).status_code == 200
    
    # delete the reservation
    assert create_reservation_EP(test_client, reservation_future_example).status_code == 200
    assert delete_reservation_EP(test_client, 2).status_code == 200


