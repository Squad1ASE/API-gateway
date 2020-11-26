from monolith.database import db, User, Restaurant, WorkingDay
from monolith.classes.tests.conftest import test_app
from monolith.utilities import create_user_EP
import json
from sqlalchemy import exc


def check_working_days(working_day_to_check, working_day):
    assert working_day_to_check.restaurant_id  == working_day.restaurant_id 
    assert working_day_to_check.day == working_day.day
    assert working_day_to_check.work_shifts == working_day.work_shifts


def test_insert_working_day(test_app):
    app, test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():
        # create a user and a restaurant to testing working_day insertions
        assert create_user_EP(test_client, email='userexampleworkingday@test.com').status_code == 200
        user_test = db.session.query(User).filter(User.email == 'userexampleworkingday@test.com').first()
        assert user_test is not None
        restaurant_dict = dict(
            owner_id = user_test.id,
            name = 'Trial Restaurant',
            lat = 22,
            lon = 22, 
            phone = '3346734121',
            cuisine_type = [Restaurant.CUISINE_TYPES(1)],
            capacity = 10,
            prec_measures = 'leggeX',
            avg_time_of_stay = 30
        )
        restaurant = Restaurant(**restaurant_dict)
        db.session.add(restaurant)
        db.session.commit()
        restaurant = db.session.query(Restaurant).first()
        assert restaurant is not None
        
        # incorrect mandatory fields with validators
        incorrect_working_days = [
            dict(restaurant_id = None, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = 0, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = -1, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = None, work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = 0, work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = 'ciao', work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = None),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = []),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [1,2]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = ['ei']),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = ('12:00','15:00')),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('ciao','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [(1,'15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00','15:00','17:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('19:00','18:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(2), work_shifts = [('8:00','10:00'),('12:00','15:00'),('19:00','23:00')])
        ]
        count_assert = 0
        for w in incorrect_working_days:
            try:
                working_day = WorkingDay(**w)
            except ValueError:
                count_assert += 1
                assert True
        assert len(incorrect_working_days) == count_assert

        # missing fields
        incorrect_working_days = [
            dict(day = WorkingDay.WEEK_DAYS(1), work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, work_shifts = [('12:00','15:00'),('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1))
        ]
        count_assert = 0
        for w in incorrect_working_days:
            working_day = WorkingDay(**w)
            try:
                db.session.add(working_day)
                db.session.commit()
            except (exc.IntegrityError, exc.InvalidRequestError):
                db.session.rollback()
                count_assert += 1
                assert True
        assert len(incorrect_working_days) == count_assert

        # correct working_days
        correct_working_days = [
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('19:00','23:00')]),
            dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(2), work_shifts = [('12:00','15:00'),('19:00','23:00')]),
        ]
        for w in correct_working_days:
            working_day = WorkingDay(**w)
            db.session.add(working_day)
            db.session.commit()
            working_day_to_check = db.session.query(WorkingDay).filter(WorkingDay.restaurant_id == working_day.restaurant_id).filter(WorkingDay.day == working_day.day).first()
            assert working_day_to_check is not None
            check_working_days(working_day_to_check, working_day)

        # the insertion of the same day for the same restaurant must fail
        w = dict(restaurant_id = restaurant.id, day = WorkingDay.WEEK_DAYS(1), work_shifts = [('19:00','23:00')])
        working_day = WorkingDay(**w)
        count_assert = 0
        try:
            db.session.add(working_day)
            db.session.commit()
        except (exc.IntegrityError, exc.InvalidRequestError):
            db.session.rollback()
            count_assert += 1
            assert True
        assert count_assert == 1

        # check total working_days
        working_days = db.session.query(WorkingDay).all()
        assert len(working_days) == len(correct_working_days)