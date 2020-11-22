def restaurant_reservations(test_client, restaurant_id):
    return test_client.get('/reservations?restaurant_id='+str(restaurant_id))

def user_reservations(test_client, user_id):
    return test_client.get('/reservations?user_d='+str(user_id))

def create_reservation(test_client, reservation):
    return test_client.put('/reservations', json=reservation)

def confirm_participants(test_client, reservation_id, participants):
    return test_client.put('/reservations/'+str(reservation_id)+'/entrances', json=participants)

reservation_example = temp_dict = dict(
    booker_id = 1,
    booker_email = 'userexample1@test.com',
    restaurant_id = 1,
    date = '20/11/2020',
    time = '12:00',
    places = 2
)

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
tables_example = [{
    'capacity':5,
    'id':1,
    'name':'yellow',
    'restaurant_id':1
}]