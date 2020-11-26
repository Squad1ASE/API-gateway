from monolith.database import db, User, Restaurant, Dish
from monolith.classes.tests.conftest import test_app
import json
from sqlalchemy import exc
from monolith.utilities import create_user_EP


def check_dishes(dish_to_check, dish):
    assert dish_to_check.restaurant_id  == dish.restaurant_id 
    assert dish_to_check.dish_name == dish.dish_name
    assert dish_to_check.price == dish.price
    assert dish_to_check.ingredients == dish.ingredients


def test_insert_dish(test_app):
    app, test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():
        # create a user and a restaurant to testing dish insertions
        assert create_user_EP(test_client, email='userexampledish@test.com').status_code == 200
        user_test = db.session.query(User).filter(User.email == 'userexampledish@test.com').first()
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

        # incorrect fields with validators
        incorrect_dishes = [
            dict(restaurant_id = None, dish_name = 'pizza', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = 0, dish_name = 'pizza', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = -1, dish_name = 'pizza', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = None, price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = '', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = None, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = 0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = -1, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = 4.0, ingredients = None),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = 4.0, ingredients = '')
        ]
        count_assert = 0
        for d in incorrect_dishes:
            try:
                dish = Dish(**d)
            except ValueError:
                count_assert += 1
                assert True
        assert len(incorrect_dishes) == count_assert


        # missing mandatory fields
        incorrect_dishes = [
            dict(dish_name = 'pizza', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = 4.0)
        ]
        count_assert = 0
        for d in incorrect_dishes:
            dish = Dish(**d)
            try:
                db.session.add(dish)
                db.session.commit()
            except (exc.IntegrityError, exc.InvalidRequestError):
                db.session.rollback()
                count_assert += 1
                assert True
        assert len(incorrect_dishes) == count_assert

        # correct dishes
        correct_dishes = [
            dict(restaurant_id = restaurant.id, dish_name = 'pizza', price = 4.0, ingredients = 'pomodoro, mozzarella'),
            dict(restaurant_id = restaurant.id, dish_name = 'p', price = 0.1, ingredients = 'p')
        ]
        for d in correct_dishes:
            dish = Dish(**d)
            db.session.add(dish)
            db.session.commit()
            dish_to_check = db.session.query(Dish).filter(Dish.id == dish.id).first()
            assert dish_to_check is not None
            check_dishes(dish_to_check, dish)

        # check total dishes
        dishes = db.session.query(Dish).all()
        assert len(dishes) == len(correct_dishes)