
from tests.conftest import test_app

from reservation.database import db_session
from sqlalchemy import exc
from unittest import mock
from unittest.mock import patch

from reservation.views.reservation import get_tables, get_workingdays
from reservation.utilities import confirm_participants, reservation_example, workingdays_example, tables_example, restaurant_reservations, user_reservations, create_reservation


@patch('reservation.views.reservation.get_tables')
@patch('reservation.views.reservation.get_workingdays')
def test_reservations(mock1, mock2, test_app):
    workingdays = workingdays_example
    tables = tables_example
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = workingdays
    mock2.return_value.status_code.return_value = 200
    mock2.return_value.json.return_value = tables
    app, test_client = test_app
    assert create_reservation(test_client, reservation_example).status_code == 200
    assert restaurant_reservations(test_client, 1).status_code == 200
    assert user_reservations(test_client, 1).status_code == 200
    # TODO:
    # add guests email via edit
    # confirm particiapnts
    # assert confirm_participants().status_code == 200
    # delete the reservation

