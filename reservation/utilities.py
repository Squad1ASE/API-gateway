import datetime
from datetime import timedelta

def restaurant_reservations_EP(test_client, restaurant_id):
    return test_client.get('/reservations?restaurant_id='+str(restaurant_id))

def user_reservations_EP(test_client, user_id):
    return test_client.get('/reservations?user_d='+str(user_id))

def create_reservation_EP(test_client, reservation):
    return test_client.put('/reservations', json=reservation)

def confirm_participants_EP(test_client, reservation_id, participants):
    return test_client.post('/reservations/'+str(reservation_id)+'/entrances', json=participants)

def edit_reservation_EP(test_client, reservation_id, info):
    return test_client.post('/reservations/'+str(reservation_id), json=info)

def delete_reservation_EP(test_client, reservation_id):
    return test_client.delete('/reservations/'+str(reservation_id))

#TODO: def delete_all_reservations(test_client, )

participants_example = [
    'userexample1@test.com',
    'test@test.com'
]

reservation_now_example = dict(
    booker_id = 1,
    booker_email = 'userexample1@test.com',
    restaurant_id = 2,
    date = datetime.datetime.now().strftime('%d/%m/%Y'),
    time = datetime.datetime.now().strftime('%H:%M'),
    places = 2
)

reservation_example = dict(
    booker_id = 1,
    booker_email = 'userexample1@test.com',
    restaurant_id = 1,
    date = '20/11/2020',
    time = '12:00',
    places = 2
)

reservation_future_example = dict(
    booker_id = 2,
    booker_email = 'userexample1@test.com',
    restaurant_id = 1,
    date = (datetime.datetime.now() + timedelta(days=1)).strftime('%d/%m/%Y'),
    time = datetime.datetime.now().strftime('%H:%M'),
    places = 2
)

edit_reservation_example = {
    'places':3,
    'booker_email':'userexample3@test.com',
    'seats_email': [
        {'guest_email':'test@test.com'},
        {'guest_email':'test2@test.com'}
    ]
}

'''
workingdays_example = [{
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
'''
tables_example = [{
    'capacity':5,
    'id':1,
    'name':'yellow',
    'restaurant_id':1
}]

restaurant_h24_example = {
    "avg_rating": 0.0,
    "avg_time_of_stay": 40,
    "capacity": 10,
    "cuisine_type": [
        "italian",
        "traditional"
    ],
    "dishes": [
        {
            "id": 1,
            "ingredients": "tomato,mozzarella",
            "name": "pizza",
            "price": 4.5,
            "restaurant_id": 2
        },
        {
            "id": 2,
            "ingredients": "pasta,tomato",
            "name": "pasta",
            "price": 6.5,
            "restaurant_id": 2
        }
    ],
    "id": 2,
    "lat": 42.42,
    "likes": 0,
    "lon": 42.42,
    "name": "Restaurant h24",
    "owner_id": 123,
    "phone": "050123456",
    "prec_measures": "Adopted the measures envisaged by the DPCM 'X'",
    "tables": [
        {
            "capacity": 5,
            "id": 1,
            "name": "yellow",
            "restaurant_id": 2
        },
        {
            "capacity": 5,
            "id": 2,
            "name": "blue",
            "restaurant_id": 2
        }
    ],
    "tot_reviews": 0,
    "working_days": [
        {
            "day": "monday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "tuesday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "wednesday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "thursday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "friday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "saturday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        },
        {
            "day": "sunday",
            "restaurant_id": 2,
            "work_shifts": [
                [
                    "00:00",
                    "23:59"
                ]
            ]
        }
    ]
}

restaurant_example = {
    "avg_rating": 0.0,
    "avg_time_of_stay": 40,
    "capacity": 5,
    "cuisine_type": [
        "italian",
        "traditional"
    ],
    "dishes": [
        {
            "id": 1,
            "ingredients": "tomato,mozzarella",
            "name": "pizza",
            "price": 4.5,
            "restaurant_id": 1
        },
        {
            "id": 2,
            "ingredients": "pasta,tomato",
            "name": "pasta",
            "price": 6.5,
            "restaurant_id": 1
        }
    ],
    "id": 1,
    "lat": 42.42,
    "likes": 0,
    "lon": 42.42,
    "name": "My Pizza Restaurant",
    "owner_id": 123,
    "phone": "050123456",
    "prec_measures": "Adopted the measures envisaged by the DPCM 'X'",
    "tables": [
        {
            "capacity": 5,
            "id": 1,
            "name": "yellow",
            "restaurant_id": 1
        }
    ],
    "tot_reviews": 0,
    "working_days": [
        {
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
        }
    ]
}