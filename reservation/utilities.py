reservation_example = temp_dict = dict(
    booker_id = 1,
    booker_email = 'admin@admin.com',
    restaurant_id = 1,
    #date = datetime.datetime.strftime(reservation_datetime),
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