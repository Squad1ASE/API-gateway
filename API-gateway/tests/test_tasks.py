import time
import unittest
from app import ( mail, compute_review_count, send_notifications, 
                            unmark_negative_users, send_email, 
                            get_mail_object, compute_like_count )
from classes.tests.conftest import test_app
from database import User, db, Restaurant, Like, Review, Notification, Quarantine

from datetime import datetime, timedelta
import datetime as dt

def add_user(email, phone, firstname, lastname, password, date,role):
    new_user = User()
    new_user.email = email
    new_user.phone = phone
    new_user.firstname = firstname
    new_user.lastname = lastname
    new_user.password = password
    new_user.role=role
    new_user.dateofbirth = date

    db.session.add(new_user)
    db.session.commit()
    return db.session.query(User).filter(User.email == email).first()

def test_send_email(test_app):
    app, test_client = test_app
    # --- UNIT TESTS ---
    with app.app_context():
        with get_mail_object().record_messages() as outbox:
            send_email('testing', 'test1', ['jackpeps@gmail.com'])
            assert len(outbox) == 1
            assert outbox[0].subject == "testing"


# del_inactive_users task is tested on test_delete_user.py 


def test_compute_like_count(test_app):
    app, test_client = test_app
    with app.app_context():


        user_test = add_user("likecountuser@test.com", '3333333333', "firstname", "lastname", "passwo",
                             datetime.now(),'customer')
        user_test1 = add_user("likecountuser1@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(),'customer')
        user_test2 = add_user("likecountuser2@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(),'customer')

        owner_test = add_user("likecountowner@test.com", '3333333333', "firstname", "lastname", "passwo",
                             datetime.now(), 'owner')
        owner_test1 = add_user("likecountowner1@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(), 'owner')

        restaurants = [
            dict(owner_id=owner_test.id, name='ciccio', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1)],
                 capacity=10, prec_measures='leggeX', avg_time_of_stay=30
                 ),
            dict(owner_id=owner_test1.id, name='pluto', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)],
                 capacity=1, prec_measures='', avg_time_of_stay=15, tot_reviews=None, avg_rating=None, likes=None
                 )
        ]

        for r in restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

        ciccio_restaurant = db.session.query(Restaurant).filter_by(name="ciccio").first()
        pluto_restaurant = db.session.query(Restaurant).filter_by(name="pluto").first()

        def putLike(user_id, restaurant_id):
            new_like = Like()
            new_like.liker_id = user_id
            new_like.restaurant_id = restaurant_id
            db.session.add(new_like)
            db.session.commit()

        assert (ciccio_restaurant.likes is not None)
        assert (pluto_restaurant.likes is not None)
        assert (ciccio_restaurant.likes == 0)
        assert (pluto_restaurant.likes == 0)

        putLike(user_test.id, ciccio_restaurant.id)
        compute_like_count()
        assert (ciccio_restaurant.likes == 1)
        assert (pluto_restaurant.likes == 0)

        putLike(user_test.id, pluto_restaurant.id)
        putLike(user_test1.id, pluto_restaurant.id)
        putLike(user_test2.id, pluto_restaurant.id)
        compute_like_count()

        pluto_restaurant = db.session.query(Restaurant).filter_by(id=pluto_restaurant.id).first()
        ciccio_restaurant = db.session.query(Restaurant).filter_by(id=ciccio_restaurant.id).first()
        assert (ciccio_restaurant.likes == 1)
        assert (pluto_restaurant.likes == 3)
        compute_like_count()

        putLike(user_test1.id, ciccio_restaurant.id)
        putLike(user_test2.id, ciccio_restaurant.id)
        compute_like_count()
        pluto_restaurant = db.session.query(Restaurant).filter_by(id=pluto_restaurant.id).first()
        ciccio_restaurant = db.session.query(Restaurant).filter_by(id=ciccio_restaurant.id).first()
        assert (ciccio_restaurant.likes == 3)
        assert (pluto_restaurant.likes == 3)


def test_compute_review_count(test_app):
    app, test_client = test_app
    with app.app_context():
        user_test = add_user("likecountuser@test.com", '3333333333', "firstname", "lastname", "passwo",
                             datetime.now(), 'customer')
        user_test1 = add_user("likecountuser1@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(), 'customer')
        user_test2 = add_user("likecountuser2@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(), 'customer')

        owner_test = add_user("likecountowner@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(), 'owner')
        owner_test1 = add_user("likecountowner1@test.com", '3333333333', "firstname", "lastname", "passwo",
                               datetime.now(), 'owner')

        restaurants = [
            dict(owner_id=owner_test.id, name='ciccio', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1)],
                 capacity=10, prec_measures='leggeX', avg_time_of_stay=30
                 ),
            dict(owner_id=owner_test1.id, name='pluto', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)],
                 capacity=1, prec_measures='', avg_time_of_stay=15, tot_reviews=None, avg_rating=None, likes=None
                 )
        ]

        for r in restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

        ciccio_restaurant = db.session.query(Restaurant).filter_by(name="ciccio").first()
        pluto_restaurant = db.session.query(Restaurant).filter_by(name="pluto").first()

        def putReview(user_id, restaurant_id, rating):
            new_review = Review()
            new_review.marked = False
            new_review.comment = 'Good quality restaurant'
            new_review.rating = rating
            new_review.date = datetime.now()
            new_review.restaurant_id = restaurant_id
            new_review.reviewer_id = user_id
            db.session.add(new_review)
            db.session.commit()

        assert (ciccio_restaurant.avg_rating is not None)
        assert (pluto_restaurant.avg_rating is not None)
        assert (ciccio_restaurant.avg_rating == 0)
        assert (pluto_restaurant.avg_rating == 0)

        putReview(user_test.id, ciccio_restaurant.id, 3)
        putReview(user_test1.id, ciccio_restaurant.id, 2)

        compute_review_count()

        pluto_restaurant = db.session.query(Restaurant).filter_by(id=pluto_restaurant.id).first()
        ciccio_restaurant = db.session.query(Restaurant).filter_by(id=ciccio_restaurant.id).first()
        assert (ciccio_restaurant.avg_rating == 2.5)
        assert (pluto_restaurant.avg_rating == 0)

        putReview(user_test.id, pluto_restaurant.id, 0)
        putReview(user_test1.id, pluto_restaurant.id, 4)
        putReview(user_test2.id, pluto_restaurant.id, 5)
        putReview(user_test2.id, ciccio_restaurant.id, 4)

        compute_review_count()

        pluto_restaurant = db.session.query(Restaurant).filter_by(id=pluto_restaurant.id).first()
        ciccio_restaurant = db.session.query(Restaurant).filter_by(id=ciccio_restaurant.id).first()
        assert (ciccio_restaurant.avg_rating == 3)
        assert (pluto_restaurant.avg_rating == 3)
        compute_review_count()
        compute_review_count()

        assert (pluto_restaurant.avg_rating == 3)
        assert (ciccio_restaurant.avg_rating == 3)


def test_send_notifications(test_app):
    app, test_client = test_app
    with app.app_context():

        user_test = add_user("g.peparaio@consorziometis.it", '3333333333', "firstname", "lastname", "passwo",
                             datetime.now(),'customer')
        user_test1 = add_user("jackpeps@gmail.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(),'customer')

        def putNotification(user_id):
            new_dict = dict(user_id=user_id, email='test@email.com', message='hello', pending=True, type_=Notification.TYPE(1),
             date=datetime.now())
            new_notification = Notification(**new_dict)
            db.session.add(new_notification)
            db.session.commit()
            return db.session.query(Notification).filter_by(user_id=user_id).first()

        firstNotification = putNotification(user_test.id)
        secondNotification = putNotification(user_test1.id)

        assert firstNotification.pending == True
        assert secondNotification.pending == True
        assert db.session.query(User).filter_by(id=user_test.id).first().is_active == True
        assert db.session.query(User).filter_by(id=user_test1.id).first().is_active == True

        assert send_notifications() == 2

        firstNotification= db.session.query(Notification).filter_by(user_id=user_test.id).first()
        secondNotification1 = db.session.query(Notification).filter_by(user_id=user_test1.id).first()
        assert firstNotification.pending == False
        assert secondNotification1.pending == False

        assert send_notifications() == 0

        firstNotification = db.session.query(Notification).filter_by(user_id=user_test.id).first()
        secondNotification1 = db.session.query(Notification).filter_by(user_id=user_test1.id).first()
        assert firstNotification.pending == False
        assert secondNotification1.pending == False




def test_unmark_negative_users(test_app):
    app, test_client = test_app
    with app.app_context():
        user_test = add_user("g.peparaio@consorziometis.it", '3333333333', "firstname", "lastname", "passwo",
                             datetime.now(), 'customer')
        user_test1 = add_user("jackpeps@gmail.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.now(), 'customer')

        def putQuarantine(user_id,end_date):
            new_quarantine = Quarantine()
            new_quarantine.user_id = user_id
            new_quarantine.start_date= dt.date.today()
            new_quarantine.end_date = end_date
            db.session.add(new_quarantine)
            db.session.commit()
            return db.session.query(Quarantine).filter_by(user_id=user_id).first()

        unmark_negative_users()

        db.session.commit()

        firstquarantine = putQuarantine(user_test.id,dt.date.today())
        secondquarantine = putQuarantine(user_test1.id,dt.date.today()+timedelta(days=1))

        unmark_negative_users()

        user_test=db.session.query(User).filter_by(id=user_test.id).first()
        user_test1= db.session.query(User).filter_by(id=user_test1.id).first()

        firstquarantine = db.session.query(Quarantine).filter_by(user_id=user_test.id).first()
        secondquarantine = db.session.query(Quarantine).filter_by(user_id=user_test1.id).first()

        assert firstquarantine.in_observation == False
        assert secondquarantine.in_observation == True
