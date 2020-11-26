from monolith.database import db, User, Quarantine, Restaurant, Notification, Reservation, Seat
from monolith.classes.tests.conftest import test_app
from monolith.utilities import restaurant_h24_example, user_logout_EP, restaurant_reservation_POST_EP, restaurant_reservation_EP, create_restaurant_EP, create_user_EP, user_login_EP, insert_ha, customers_example, restaurant_example, restaurant_owner_example, health_authority_example,  mark_patient_as_positive
import datetime
from sqlalchemy import exc
from datetime import timedelta


def test_mark_positive(test_app):
    app, test_client = test_app
    
    # create a health authority and an user for testing 
    temp_ha_dict = dict(
        email='healthauthority@ha.com',
        phone='3333333333',
        firstname='Ha',
        lastname='Ha',
        password='ha',
        dateofbirth='05/10/2000',
        role='ha'
    )
    temp_user_example_dict = customers_example[0]
    #assert create_user_EP(test_client, **temp_ha_dict).status_code == 200 
    insert_ha(db,app)
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200

    # --- UNIT TESTS ---
    with app.app_context():
        # mark a wrong user user that doesn't exist
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

        # get the user to be marked as positive
        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()
        
        assert getuser is not None

        new_quarantine = Quarantine()
        new_quarantine.user_id = getuser.id
        today = datetime.date.today()
        new_quarantine.start_date = today
        new_quarantine.end_date = today + datetime.timedelta(days=14)
        new_quarantine.in_observation = True

        db.session.add(new_quarantine)
        db.session.commit()

        getquarantine = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id).first()
        assert getquarantine is not None
        assert getquarantine.start_date == today
        assert getquarantine.end_date == today + datetime.timedelta(days=14)
        assert getquarantine.in_observation == True

        # change in_observation state, so the user can use the app again
        getquarantine.in_observation = False
        db.session.commit()

        getquarantinenewstatus = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id).first()
        assert getquarantinenewstatus.in_observation == False
    
    # --- COMPONENTS TESTS ---


def test_component_health_authority(test_app):

    app, test_client = test_app

    # create a health authority and an user for testing
    temp_user_example_dict = customers_example[0]
    #assert create_user_EP(test_client, **temp_ha_dict).status_code == 200 
    insert_ha(db,app)
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200
    temp_user_example_dict = customers_example[1]
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200

    # access to patient information is forbidden for customers
    user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])
    
    result = test_client.get('/patient_informations', follow_redirects=True)
    assert result.status_code == 403

    test_client.get('/logout', follow_redirects=True)

    # access to health authority is allowed
    user_login_EP(test_client, "healthauthority@ha.com", "ha")

    result = test_client.get('/patient_informations', follow_redirects=True)
    assert result.status_code == 200

    # wrong email must return patient not found
    result = test_client.post('/patient_informations', data=dict(email="wrongemail@test.com"), follow_redirects=True)
    assert result.status_code == 404

    # try to mark the health authority itself
    result = test_client.post('/patient_informations', data=dict(email="healthauthority@ha.com"), follow_redirects=True)
    assert result.status_code == 403
    
    # correct email must returns the patient informations 
    result = test_client.post('/patient_informations', data=dict(email=temp_user_example_dict['email']), follow_redirects=True)
    assert result.status_code == 200

    # patient 1 is marked as positive 
    assert mark_patient_as_positive(test_client, customers_example[0]['email']).status_code == 555
    #result = test_client.post('/patient_informations?email=userexample1%40test.com', data=dict(mark_positive_button='mark_positive'), follow_redirects=True)
    #assert result.status_code == 555

    # patient 2 is marked as positive 
    assert mark_patient_as_positive(test_client, customers_example[1]['email']).status_code == 555

    # a patient already marked will return a different html
    result = test_client.post('/patient_informations', data=dict(email=temp_user_example_dict['email']), follow_redirects=True)
    assert result.status_code == 200

    # go to the previous page when patient is already marked as positive
    result = test_client.get('/patient_informations?email=userexample1%40test.com', data=dict(go_back_button='go_back'), follow_redirects=True)
    assert result.status_code == 200


def test_contact_tracing_health_authority(test_app):
    app, test_client = test_app

    # create a health authority and an user for testing
    temp_user_example_dict = customers_example[0]
    #assert create_user_EP(test_client, **temp_ha_dict).status_code == 200 
    insert_ha(db,app)
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200
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

    # make reservation 1
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

    # confirm the guests
    with app.app_context():
        seats = db.session.query(Seat).all()
        for s in seats:
            s.confirmed = True
        db.session.commit()


    # make reservation 2
    date = datetime.datetime.now() + timedelta(days=2)
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


    # login ha
    user_logout_EP(test_client)
    assert user_login_EP(test_client, "healthauthority@ha.com", "ha").status_code == 200

    # mark positive
    assert mark_patient_as_positive(test_client, temp_user_example_dict['email']).status_code == 555

    # test notification
    with app.app_context():
        notifications = db.session.query(Notification).all()
        for n in notifications:
            print(n.message)
        assert len(notifications) == 3