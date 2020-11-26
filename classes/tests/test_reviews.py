from monolith.database import db, User, Restaurant, Review
from monolith.classes.tests.conftest import test_app
from monolith.utilities import (restaurant_reservation_POST_EP, restaurant_reservation_EP, 
                                insert_ha, create_review_EP, create_user_EP, user_login_EP, 
                                create_restaurant_EP, customers_example, restaurant_example, 
                                restaurant_owner_example, reservation_dates_example, 
                                reservation_guests_number_example, reservation_times_example )
import json
from sqlalchemy import exc
import datetime

def test_unit_reviews(test_app):
    app, test_client = test_app

    assert create_user_EP(test_client, **restaurant_owner_example[0]).status_code == 200
    assert user_login_EP(test_client, restaurant_owner_example[0]['email'], restaurant_owner_example[0]['password']).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200

    with app.app_context():

        # get a restaurant
        restaurant = db.session.query(Restaurant).filter_by(name = restaurant_example[0]['name']).first()
        #get a user
        user = db.session.query(User).filter_by(email=restaurant_owner_example[0]['email']).first()

        new_review = Review()
        new_review.marked = False
        new_review.comment = 'Good quality restaurant'
        new_review.rating = 3
        new_review.date = datetime.date.today()
        new_review.restaurant_id = restaurant.id
        new_review.reviewer_id = user.id
        db.session.add(new_review)
        db.session.commit()

        review = Review.query.filter_by(restaurant_id = int(restaurant.id)).first()

        assert review.marked == False
        assert review.comment == 'Good quality restaurant'
        assert review.rating == 3
        assert review.date == datetime.date.today()
        assert review.restaurant_id == restaurant.id
        assert review.reviewer_id == user.id

def test_component_reviews(test_app):
    app, test_client = test_app

    assert create_user_EP(test_client, **restaurant_owner_example[0]).status_code == 200
    assert user_login_EP(test_client, restaurant_owner_example[0]['email'], restaurant_owner_example[0]['password']).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200

    review = dict(
        rating=4,
        comment='Good quality restaurant',
        date=datetime.date.today()
    )

    uncorrect_review = dict(
        rating=10,
        comment='Good quality restaurant',
        date=datetime.date.today()
    )


    with app.app_context():
        # get a restaurant
        restaurant = db.session.query(Restaurant).filter_by(name = restaurant_example[0]['name']).first()
        #get a user, the owner
        user = db.session.query(User).filter_by(email=restaurant_owner_example[0]['email']).first()

    # try to get as a owner (555)
    assert test_client.get('/restaurants/reviews/'+str(restaurant.id), follow_redirects=True).status_code == 555

    # try to review a place when i'm a owner (403)
    assert create_review_EP(test_client, review, restaurant.id).status_code == 403

    # logout with the owner (200)
    assert test_client.get('/logout', follow_redirects=True).status_code == 200
    
    # create a customer
    assert create_user_EP(test_client, **customers_example[0]).status_code == 200

    # login with the customer (200)
    assert user_login_EP(test_client, customers_example[0]['email'], customers_example[0]['password']).status_code == 200

    # try to get as a customer without a reservation (555)
    assert test_client.get('/restaurants/reviews/'+str(restaurant.id)).status_code == 555
    assert create_review_EP(test_client, review, restaurant.id).status_code == 403

    # create a reservation in the future (200)
    assert restaurant_reservation_EP(test_client, 
                                     restaurant.id, 
                                     '10/10/2030',
                                     reservation_times_example[0], 
                                     reservation_guests_number_example[0]).status_code == 200

    reservation_date_str = '10/10/2030' + " " + reservation_times_example[14]
    assert restaurant_reservation_POST_EP(
        test_client,
        str(restaurant.id),
        '8',
        reservation_date_str,
        '1',
        customers_example[0]['email']
    ).status_code == 666

    # try to review when i'm not been there yet
    assert test_client.get('/restaurants/reviews/'+str(restaurant.id)).status_code == 555

    # create a reservation in the past(200)
    assert restaurant_reservation_EP(test_client, 
                                     restaurant.id, 
                                     '10/10/2020',
                                     reservation_times_example[0], 
                                     reservation_guests_number_example[0]).status_code == 200

    reservation_date_str = '10/10/2020' + " " + reservation_times_example[14]
    assert restaurant_reservation_POST_EP(
        test_client,
        str(restaurant.id),
        '8',
        reservation_date_str,
        '1',
        customers_example[0]['email']
    ).status_code == 666

    # try to send an invalid form (400)
    assert create_review_EP(test_client, uncorrect_review, restaurant.id).status_code == 400

    # try to get as a customer who has a reservation (200)
    assert test_client.get('/restaurants/reviews/'+str(restaurant.id), follow_redirects=True).status_code == 200
    assert create_review_EP(test_client, review, restaurant.id).status_code == 200
    assert test_client.get('/restaurants/like/'+str(restaurant.id)).status_code == 200
    assert test_client.get('/restaurants/like/'+str(restaurant.id)).status_code == 200

    assert test_client.get('/restaurants', follow_redirects=True).status_code == 200

    # try to double review the same restaurant (403)
    assert create_review_EP(test_client, review, restaurant.id).status_code == 403

    # logout
    assert test_client.get('/logout', follow_redirects=True).status_code == 200

    insert_ha(db, app)

    # login as health authority
    assert user_login_EP(test_client, "healthauthority@ha.com", "ha").status_code == 200

    # try to get as health authority (555)
    assert test_client.get('/restaurants/reviews/'+str(restaurant.id)).status_code == 403
    assert test_client.get('/restaurants/'+str(restaurant.id)).status_code == 403
    assert test_client.get('/restaurants/'+str(restaurant.id)+'/reservation').status_code == 403
    assert test_client.get('/restaurants/like/'+str(restaurant.id)).status_code == 403

    # try to post as health authority (403)
    assert create_review_EP(test_client, review, restaurant.id).status_code == 403

        

