from monolith.database import db, User, Restaurant, WorkingDay, Table, Dish, Notification, Seat
from monolith.classes.tests.conftest import test_app
from monolith.utilities import restaurant_h24_example, insert_admin, user_logout_EP, restaurant_reservation_POST_EP, restaurant_reservation_EP, create_restaurant_EP, create_user_EP, user_login_EP, insert_ha, customers_example, restaurant_example, restaurant_owner_example, health_authority_example,  mark_patient_as_positive
import json
from sqlalchemy import exc
import datetime
from datetime import timedelta

def test_component_home(test_app):
    app, test_client = test_app
    
    assert test_client.get('/', follow_redirects=True).status_code == 200


    # normal user
    assert create_user_EP(test_client).status_code == 200
    assert user_login_EP(test_client).status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200


    # admin
    assert test_client.get('/logout', follow_redirects=True)
    #assert create_user_EP(test_client, email='admin@admin.com', password='admin',role='admin').status_code == 200
    insert_admin(db, app)
    assert user_login_EP(test_client, 'admin@admin.com', 'admin').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200


    # owner
    assert test_client.get('/logout', follow_redirects=True).status_code == 200
    assert create_user_EP(test_client, email='owner@owner.com', password='owner',role='owner').status_code == 200
    assert user_login_EP(test_client, 'owner@owner.com', 'owner').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    

    # ha -- to test the whole home I have to make reservations and mark positives
    assert test_client.get('/logout', follow_redirects=True)
    insert_ha(db,app)
    temp_user_example_dict = customers_example[1]
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200
 
    # create a owner and login
    temp_owner_example_dict = restaurant_owner_example[0]
    assert create_user_EP(test_client, **temp_owner_example_dict).status_code == 200
    assert user_login_EP(test_client, temp_owner_example_dict['email'], temp_owner_example_dict['password']).status_code == 200
    
    # create a restaurant
    temp_restaurant_example = restaurant_h24_example
    assert create_restaurant_EP(test_client, temp_restaurant_example).status_code == 200

    restaurant = None
    with app.app_context():
        restaurant = db.session.query(Restaurant).filter(Restaurant.name == temp_restaurant_example['name']).first()
    assert restaurant is not None 

    # login user
    user_logout_EP(test_client)
    assert user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password']).status_code == 200

    # make a reservation 1
    date = datetime.datetime.now() - timedelta(days=2)
    timestamp = date.strftime("%d/%m/%Y")
    assert restaurant_reservation_EP(test_client, 
                                     restaurant.id, 
                                     timestamp,
                                     '20:00', 
                                     '2').status_code == 200

    reservation_date_str = timestamp + ' 20:00'
    assert restaurant_reservation_POST_EP(
        test_client,
        str(restaurant.id),
        '1',
        reservation_date_str,
        '2',
        { 'guest1':'notified01@ex.com'}
    ).status_code == 666

    # make a reservation 2
    date = datetime.datetime.now() - timedelta(days=1)
    timestamp = date.strftime("%d/%m/%Y")
    assert restaurant_reservation_EP(test_client, 
                                     restaurant.id, 
                                     timestamp,
                                     '20:00', 
                                     '3').status_code == 200

    reservation_date_str = timestamp + ' 20:00'
    assert restaurant_reservation_POST_EP(
        test_client,
        str(restaurant.id),
        '1',
        reservation_date_str,
        '3',
        { 'guest1':'notified01@ex.com', 'guest2':customers_example[0]['email']}
    ).status_code == 666

    # make a reservation 3
    date = datetime.datetime.now() - timedelta(days=4)
    timestamp = date.strftime("%d/%m/%Y")
    assert restaurant_reservation_EP(test_client, 
                                     restaurant.id, 
                                     timestamp,
                                     '20:00', 
                                     '3').status_code == 200

    reservation_date_str = timestamp + ' 20:00'
    assert restaurant_reservation_POST_EP(
        test_client,
        str(restaurant.id),
        '1',
        reservation_date_str,
        '3',
        { 'guest1':'notified01@ex.com', 'guest2':customers_example[0]['email']}
    ).status_code == 666

    # a fake notification with user_id not associated with a real user  
    with app.app_context():
        new_notification = Notification()
        new_notification.user_id = 20
        new_notification.message = 'message ' + timestamp + ' blabla'
        new_notification.email = 'testnot@trial.com'
        new_notification.pending = True
        new_notification.type_ = Notification.TYPE(1)
        new_notification.date = datetime.date.today()
        db.session.add(new_notification)
        db.session.commit() 

    # confirm the guests
    with app.app_context():
        seats = db.session.query(Seat).all()
        for s in seats:
            s.confirmed = True
        db.session.commit()

    # login ha
    user_logout_EP(test_client)
    assert user_login_EP(test_client, "healthauthority@ha.com", "ha").status_code == 200

    # mark positive
    assert mark_patient_as_positive(test_client, temp_user_example_dict['email']).status_code == 555

    # test home ha
    assert test_client.get('/', follow_redirects=True).status_code == 200