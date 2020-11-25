from database import User
import datetime


# --- UTILITIES USER ---
def insert_admin(db, app):
    with app.app_context():
        admin = db.session.query(User).filter_by(email='admin@admin.com').first()
        if admin is None:
            example = User()
            example.email = 'admin@admin.com'
            example.phone = '3333333333'
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.set_password('admin')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.is_admin = True
            example.role = 'admin'
            db.session.add(example)
            db.session.commit()

def insert_ha(db, app):
    with app.app_context():
        ha = db.session.query(User).filter_by(email='healthauthority@ha.com').first()
        if ha is None:
            example = User()
            example.email = 'healthauthority@ha.com'
            example.phone = '3333333333'
            example.firstname = 'ha'
            example.lastname = 'ha'
            example.set_password('ha')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.is_admin = True
            example.role = 'ha'
            db.session.add(example)
            db.session.commit()

# customers
customers_example = [
    dict(
        email='userexample1@test.com',
        phone='39111111',
        firstname='firstname_test1',
        lastname='lastname_test1',
        password='passw1',
        dateofbirth='05/10/2001',
        role='customer'
    ),
    dict(
        email='userexample2@test.com',
        phone='39222222',
        firstname='firstname_test2',
        lastname='lastname_test2',
        password='passw2',
        dateofbirth='05/10/2002',
        role='customer'
    ),
    dict(
        email='userexample3@test.com',
        phone='39333333',
        firstname='firstname_test3',
        lastname='lastname_test3',
        password='passw3',
        dateofbirth='05/10/2003',
        role='customer'
    ),
    dict(
        email='userexample4@test.com',
        phone='39444444',
        firstname='firstname_test4',
        lastname='lastname_test4',
        password='passw4',
        dateofbirth='05/10/2004',
        role='customer'
    )
]       

# restaurant owner
restaurant_owner_example = [
    dict(
        email='restaurantowner1@test.com',
        phone='40111111',
        firstname='owner_firstname_test1',
        lastname='owner_lastname_test1',
        password='passw1',
        dateofbirth='05/10/2001',
        role='owner'
    ),
    dict(
        email='restaurantowner2@test.com',
        phone='40222222',
        firstname='owner_firstname_test2',
        lastname='owner_lastname_test2',
        password='passw2',
        dateofbirth='05/10/2002',
        role='owner'
    ),
    dict(
        email='restaurantowner3@test.com',
        phone='40333333',
        firstname='owner_firstname_test3',
        lastname='owner_lastname_test3',
        password='passw3',
        dateofbirth='05/10/2003',
        role='owner'
    ),
    dict(
        email='restaurantowner4@test.com',
        phone='40444444',
        firstname='owner_firstname_test4',
        lastname='owner_lastname_test4',
        password='passw4',
        dateofbirth='05/10/2004',
        role='owner'
    )
]       

# health authority
health_authority_example = dict(
    email='healthauthority@ha.com',
    phone='66666',
    firstname='Ha',
    lastname='Ha',
    password='ha',
    dateofbirth='05/10/2000',
    role='ha'
)
# admin 
admin_example = dict(
    email='badmin@admin.com',
    phone='666',
    firstname='badministrator_fn',
    lastname='badministrator_ln',
    password='badminpassw',
    dateofbirth='05/10/2001',
    role='admin'
)

def create_user_EP(
        test_client, email=customers_example[0]['email'], phone=customers_example[0]['phone'],firstname=customers_example[0]['firstname'], 
        lastname=customers_example[0]['lastname'], password=customers_example[0]['password'], dateofbirth=customers_example[0]['dateofbirth'],
        role=customers_example[0]['role']
    ):
    data = dict(
        email=email,
        phone=phone,
        firstname=firstname,
        lastname=lastname,
        password=password,
        dateofbirth=dateofbirth,
        role=role
    )
    return test_client.post('/create_user', data=data, follow_redirects=True)


def user_login_EP(test_client, email=customers_example[0]['email'], password=customers_example[0]['password']):
    data = dict(
        email=email,
        password=password
    )
    return test_client.post('/login', data=data, follow_redirects=True)

def user_logout_EP(test_client):
    return test_client.get('/logout', follow_redirects=True)

def edit_user_EP(
    test_client, phone, old_passw, new_passw
):
    data = dict(
        phone=phone,
        old_password=old_passw,
        new_password=new_passw
    )
    return test_client.post('/edit_user_informations', data=data, follow_redirects=True)


# --- UTILITIES RESTAURANT  ---
'''
restaurant_example = [
    { 
        'name':'Restaurant 1', 'lat':43.7216621, 'lon':10.4083723, 'phone':'111111', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(6)], 'prec_measures':'leggeX', 'avg_time_of_stay':15,
        'tables-0-table_name':'res1red', 'tables-0-capacity':2, 
        'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro, mozzarella',
        'dishes-1-dish_name':'pasta agli scampi', 'dishes-1-price':4, 'dishes-1-ingredients':'pasta, scampi',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(2), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(3), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(4), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(5), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(6), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-6-day': WorkingDay.WEEK_DAYS(7), 'workingdays-6-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    },
    { 
        'name':'Restaurant 2', 'lat':43.7176394, 'lon':10.4032292, 'phone':'222222', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(3)], 'prec_measures':'leggeX', 'avg_time_of_stay':25,
        'tables-0-table_name':'res2red', 'tables-0-capacity':6, 
        'tables-1-table_name':'res2blue', 'tables-1-capacity':4, 
        'dishes-0-dish_name':'pasta al pesto', 'dishes-0-price':4, 'dishes-0-ingredients':'pasta, pesto, basilico',
        'dishes-1-dish_name':'burrito', 'dishes-1-price':3, 'dishes-1-ingredients':'carne,fagioli',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(2), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(3), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(4), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(5), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(6), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-6-day': WorkingDay.WEEK_DAYS(7), 'workingdays-6-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    },
    { 
        'name':'Restaurant 3', 'lat':43.7176589, 'lon':10.4015256, 'phone':'333333', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(2)], 'prec_measures':'leggeX', 'avg_time_of_stay':40,
        'tables-0-table_name':'res3green', 'tables-0-capacity':4, 
        'tables-1-table_name':'res3red', 'tables-1-capacity':4, 
        'tables-2-table_name':'res3blue', 'tables-2-capacity':6, 
        'tables-3-table_name':'res3yellow', 'tables-3-capacity':10, 
        'dishes-0-dish_name':'riso', 'dishes-0-price':4, 'dishes-0-ingredients':'funghi',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(2), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(3), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(4), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(5), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(6), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(7), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    },
    { 
        'name':'Restaurant 4', 'lat':43.7174589, 'lon':10.4012256, 'phone':'444444', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(4),Restaurant.CUISINE_TYPES(5)], 'prec_measures':'leggeX', 'avg_time_of_stay':15,
        'tables-0-table_name':'res4green', 'tables-0-capacity':4, 
        'tables-1-table_name':'res4red', 'tables-1-capacity':4, 
        'tables-2-table_name':'res4blue', 'tables-2-capacity':4,
        'dishes-0-dish_name':'panino con carne', 'dishes-0-price':3, 'dishes-0-ingredients':'pane, carne',
        'dishes-1-dish_name':'panino con pesce', 'dishes-1-price':3, 'dishes-1-ingredients':'pane, pesce',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(2), 'workingdays-0-work_shifts':"('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(3), 'workingdays-1-work_shifts':"('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(5), 'workingdays-2-work_shifts':"('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(6), 'workingdays-3-work_shifts':"('19:00','23:00')"
    }
]

restaurant_h24_example = {
    'name':'Restaurant h24', 'lat':43.7216621, 'lon':10.4083723, 'phone':'111111', 
    'cuisine_type':[Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(6)], 'prec_measures':'leggeX', 'avg_time_of_stay':15,
    'tables-0-table_name':'res1red', 'tables-0-capacity':2, 
    'tables-1-table_name':'res24blu', 'tables-1-capacity':4, 
    'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro, mozzarella',
    'dishes-1-dish_name':'pasta agli scampi', 'dishes-1-price':4, 'dishes-1-ingredients':'pasta, scampi',
    'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('00:00','23:59')",
    'workingdays-1-day': WorkingDay.WEEK_DAYS(2), 'workingdays-1-work_shifts':"('00:00','23:59')",
    'workingdays-2-day': WorkingDay.WEEK_DAYS(3), 'workingdays-2-work_shifts':"('00:00','23:59')",
    'workingdays-3-day': WorkingDay.WEEK_DAYS(4), 'workingdays-3-work_shifts':"('00:00','23:59')",
    'workingdays-4-day': WorkingDay.WEEK_DAYS(5), 'workingdays-4-work_shifts':"('00:00','23:59')",
    'workingdays-5-day': WorkingDay.WEEK_DAYS(6), 'workingdays-5-work_shifts':"('00:00','23:59')",
    'workingdays-6-day': WorkingDay.WEEK_DAYS(7), 'workingdays-6-work_shifts':"('00:00','23:59')"
}
'''
reservation_dates_example = [
    '09/11/2020',
    '10/11/2020',
    '11/11/2020',
    '12/11/2020',
    '13/11/2020',
    '14/11/2020',
    '15/11/2020',
    '17/11/2020'
]

reservation_times_example = [
    '12:00',
    '12:05',
    '12:10',
    '12:16',
    '12:30',
    '13:00',
    '13:03',
    '13:08',
    '13:20',
    '13:33',
    '13:50',
    '14:20',
    '14:40',
    '15:00',
    '19:00',
    '19:02',
    '19:13',
    '19:18',
    '19:33',
    '19:40',
    '19:57',
    '20:20',
    '20:31',
    '20:40',
    '21:30',
    '21:40',
    '21:50',
    '22:30',
    '23:50'
]

reservation_guests_number_example = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    9,
    10,
    11,
    12,
    13,
    14
]

reservation_guests_email_example = [
    'guestemail1@test.com',
    'guestemail2@test.com',
    'guestemail3@test.com',
    'guestemail4@test.com',
    'guestemail5@test.com',
    'guestemail6@test.com',
    'guestemail7@test.com',
    'guestemail8@test.com',
    'guestemail9@test.com',
    'guestemail10@test.com',
    'guestemail11@test.com',
    'guestemail12@test.com',
    'guestemail13@test.com',
    'guestemail14@test.com'
]

'''
reservations_example = [
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
    dict(
        date='27/10/2020',
        time='14:00',
        guests=2
    ),
]
'''



# recall: to call this function you must be logged in
'''
def create_restaurant_EP(test_client, data_dict=restaurant_example[0]):
    return test_client.post('/create_restaurant', data=data_dict, follow_redirects=True)


def restaurant_reservation_EP(test_client, restaurant_id, date, time, guests):
    data = dict(date=date,time=time,guests=guests)
    return test_client.post('/restaurants/'+str(restaurant_id), data=data, follow_redirects=True)


def restaurant_reservation_GET_EP(test_client, restaurant_id, table_id_reservation, date, guests):
    return test_client.get('/restaurants/'+restaurant_id+'/reservation?table_id='+str(table_id_reservation)+'&'+'guests='+str(guests)+'&'+'date='+date, follow_redirects=True)


def restaurant_reservation_POST_EP(test_client, restaurant_id, table_id_reservation, date, guests, data):
    return test_client.post('/restaurants/'+restaurant_id+'/reservation?table_id='+str(table_id_reservation)+'&'+'guests='+str(guests)+'&'+'date='+date, data=data, follow_redirects=True)
'''

def create_review_EP(test_client, data_dict, rest_id):
    return test_client.post('/restaurants/reviews/'+str(rest_id), data=data_dict, follow_redirects=True)

def confirm_participants_EP(test_client, restaurant_id, reservation_id, data_dict):
    return test_client.post('/restaurants/' + str(restaurant_id) + '/reservation/' + str(reservation_id), data=data_dict, follow_redirects=True)


# --- UTILITIES HEALTHAUTHORITY ---
def mark_patient_as_positive(test_client, patient_mail):
    email = patient_mail.replace('@', '%40')
    return test_client.post('/patient_informations?email='+email, data=dict(mark_positive_button='mark_positive'), follow_redirects=True)


