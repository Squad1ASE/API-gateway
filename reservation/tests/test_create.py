
from tests.conftest import test_app

from database import db_session
from sqlalchemy import exc
from unittest import mock
from unittest.mock import patch

from views.reservation import create_reservation, get_tables, get_workingdays
from utilities import reservation_example, workingdays_example, tables_example


@patch('views.reservation.get_tables')
@patch('views.reservation.get_workingdays')
def test_create(mock1, mock2, test_app):
    app, test_client = test_app
    workingdays = workingdays_example
    tables = tables_example
    mock1.return_value.status_code.return_value = 200
    mock1.return_value.json.return_value = workingdays
    mock2.return_value.status_code.return_value = 200
    mock2.return_value.json.return_value = tables
    #with app.test_request_context():
    #    assert create_reservation(1).status_code == 200
    assert test_client.put('/reservations/users/1', json=reservation_example).status_code == 200




'''
def test_unit_create(test_app):
    app, test_client = test_app
    tables = [{
        'capacity':5,
        'id':1,
        'name':'yellow',
        'restaurant_id':1
    }]
    workingdays = [{
            "day": "friday",
            "restaurant_id": 1,
            "work_shifts": [
                [
                    "12:00",
                    "15:00"
                ],
                [
                    "19:00",
                    "23:00"
                ]
            ]
        },
        {
            "day": "saturday",
            "restaurant_id": 1,
            "work_shifts": [
                [
                    "12:00",
                    "15:00"
                ],
                [
                    "19:00",
                    "23:00"
                ]
            ]
    }]
    with mock.patch('views.reservation.get_workingdays', status_code = 200, json = workingdays) as mock_wds:
       with mock.patch('views.reservation.get_tables', status_code = 200, json = tables) as mock_tbs:
            print(test_client.put('/reservations/users/1', json=reservation_example))
'''

