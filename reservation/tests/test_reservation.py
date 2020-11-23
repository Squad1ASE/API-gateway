
from tests.conftest import test_app

from reservation.database import db_session, Reservation, Seat
from sqlalchemy import exc
from unittest import mock
from unittest.mock import patch
import datetime

from reservation.views.reservation import get_tables, get_workingdays, get_restaurant, create_reservation
from reservation.utilities import restaurant_example, confirm_participants_EP, reservation_example, tables_example, restaurant_reservations_EP, user_reservations_EP, create_reservation_EP

@patch('reservation.views.reservation.get_tables')
@patch('reservation.views.reservation.get_restaurant')
def test_unit_reservations(mock1, mock2, test_app):
    tables = tables_example
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = restaurant_example
    mock2.return_value.status_code.return_value = 200
    mock2.return_value.json.return_value = tables
    app, test_client = test_app
    with app.test_request_context(json=reservation_example):
        assert create_reservation()
    reservation = db_session.query(Reservation).first()
    assert reservation is not None
    assert reservation.id == 1
    assert reservation.restaurant_id == 1
    assert reservation.date == datetime.datetime(2020, 11, 20, 12, 0)
    assert reservation.places == 2

@patch('reservation.views.reservation.get_tables')
#@patch('reservation.views.reservation.get_workingdays')
@patch('reservation.views.reservation.get_restaurant')
def test_component_reservations(mock1, mock2, test_app):
    tables = tables_example
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = restaurant_example
    mock2.return_value.status_code.return_value = 200
    mock2.return_value.json.return_value = tables
    app, test_client = test_app
    assert create_reservation_EP(test_client, reservation_example).status_code == 200
    assert restaurant_reservations_EP(test_client, 1).status_code == 200
    assert user_reservations_EP(test_client, 1).status_code == 200
    # TODO:
    # add guests email via edit
    # confirm participants
    # assert confirm_participants_EP().status_code == 200
    # delete the reservation

