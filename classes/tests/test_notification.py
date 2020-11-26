from monolith.database import db, User, Notification
from monolith.classes.tests.conftest import test_app 
from monolith.utilities import create_user_EP
import json
from sqlalchemy import exc
import datetime


def check_notifications(notification_to_check, notification):
    assert notification_to_check.user_id  == notification.user_id 
    assert notification_to_check.email == notification.email
    assert notification_to_check.message == notification.message
    assert notification_to_check.pending  == notification.pending 
    assert notification_to_check.type_ == notification.type_
    assert notification_to_check.date == notification.date


def test_insert_notification(test_app):
    app, test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():
        # create a user to test notification insertions
        assert create_user_EP(test_client, email='userexamplenotification@test.com').status_code == 200
        user_test = db.session.query(User).filter(User.email == 'userexamplenotification@test.com').first()
        assert user_test is not None

        # incorrect fields with validators
        incorrect_notifications = [
            dict(user_id = 0, email = 'test@email.com', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = -1, email = 'test@email.com', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = None, message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = '', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'wrongemail', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = None, pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = '', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = None, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = True, type_ = None, date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = True, type_ = 1, date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = True, type_ = 'hei', date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = None)
        ]
        count_assert = 0
        for n in incorrect_notifications:
            try:
                notification = Notification(**n)
            except ValueError:
                count_assert += 1
                assert True
        assert len(incorrect_notifications) == count_assert

        # missing mandatory fields
        incorrect_notifications = [
            dict(message = 'hello', type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(email = 'test@email.com', type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(email = 'test@email.com', message = 'hello', date = datetime.date(2020, 10, 5)),
            dict(email = 'test@email.com', message = 'hello', type_ = Notification.TYPE(1))
        ]
        count_assert = 0
        for n in incorrect_notifications:
            notification = Notification(**n)
            try:
                db.session.add(notification)
                db.session.commit()
            except (exc.IntegrityError, exc.InvalidRequestError):
                db.session.rollback()
                count_assert += 1
                assert True
        assert len(incorrect_notifications) == count_assert

        # correct notifications
        correct_notifications = [
            dict(user_id = user_test.id, email = 'test@email.com', message = 'hello', pending = True, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(email = 'test@email.com', message = 'hello', type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
            dict(user_id = user_test.id, email = 'test@email.com', message = 'h', pending = False, type_ = Notification.TYPE(1), date = datetime.date(2020, 10, 5)),
        ]
        for n in correct_notifications:
            notification = Notification(**n)
            db.session.add(notification)
            db.session.commit()
            notification_to_check = db.session.query(Notification).filter(Notification.id == notification.id).first()
            assert notification_to_check is not None
            check_notifications(notification_to_check, notification)

        # check total notifications
        notifications = db.session.query(Notification).all()
        assert len(notifications) == len(correct_notifications)