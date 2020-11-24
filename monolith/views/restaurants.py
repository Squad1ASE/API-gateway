import json

from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, User, Review, Restaurant, Like, WorkingDay, Table, Dish, Seat, Reservation, Quarantine, Notification
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import (DishForm, UserForm, RestaurantForm, ReservationPeopleEmail, 
                            SubReservationPeopleEmail, ReservationRequest, RestaurantSearch, 
                            EditRestaurantForm, ReviewForm )
from monolith.views import auth
import datetime
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
import ast
import time
import datetime
from time import mktime
from datetime import timedelta
from sqlalchemy import or_
import requests
import os

restaurants = Blueprint('restaurants', __name__)

RESTAURANT_SERVICE = "http://0.0.0.0:5060/"
#RESERVATION_SERVICE = 'http://127.0.0.1:5100/'
RESERVATION_SERVICE = os.environ['RESERVATION_SERVICE']

def _check_working_days(form_working_days):
    working_days_to_add = []
    
    for wd in form_working_days:
        new_wd = WorkingDay()
        str_shifts = '[' + wd['work_shifts'] + ']'
        shifts = list(ast.literal_eval(str_shifts))
        new_wd.work_shifts = shifts
        new_wd.day = wd['day']

        working_days_to_add.append(new_wd)

    return working_days_to_add


def _check_tables(form_tables):
    tables_to_add = []
    tot_capacity = 0

    for table in form_tables:
        new_table = Table(**table)
        tot_capacity += new_table.capacity
        tables_to_add.append(new_table)

    return tables_to_add, tot_capacity


def _check_dishes(form_dishes):
    dishes_to_add = []

    for dish in form_dishes:
        new_dish = Dish(**dish)
        dishes_to_add.append(new_dish)

    return dishes_to_add


@restaurants.route('/create_restaurant', methods=['GET','POST'])
def create_restaurant():
    if current_user is not None and hasattr(current_user, 'id'):
        if (current_user.role == 'customer' or current_user.role == 'ha'):
            return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)

        form = RestaurantForm()

        if request.method == 'POST':

            if form.validate_on_submit():

                # if one or more fields that must not be present are
                must_not_be_present = ['owner_id', 'capacity', 'tot_reviews', 'avg_rating', 'likes']
                if any(k in must_not_be_present for k in request.form):
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                working_days_to_add = []
                tables_to_add = []
                dishes_to_add = []
                new_restaurant = Restaurant()

                # check that all restaurant/working days/tables/dishes fields are correct
                try:
                    working_days_to_add = _check_working_days(form.workingdays.data)
                    del form.workingdays

                    tables_to_add, tot_capacity = _check_tables(form.tables.data)
                    del form.tables

                    dishes_to_add = _check_dishes(form.dishes.data)
                    del form.dishes

                    form.populate_obj(new_restaurant)
                    new_restaurant.owner_id = current_user.id
                    new_restaurant.capacity = tot_capacity
                except:
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                db.session.add(new_restaurant)
                db.session.commit()

                # database check when insert the tables and dishes
                for l in [working_days_to_add, tables_to_add, dishes_to_add]:
                    for el in l:
                        el.restaurant_id = new_restaurant.id
                        db.session.add(el)
                db.session.commit()
                return redirect('/')

            else:
                # invalid form
                return make_response(render_template('create_restaurant.html', form=form), 400)

        return render_template('create_restaurant.html', form=form)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


@restaurants.route('/restaurants')
@login_required
def _restaurants(message=''):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    
    allrestaurants = db.session.query(Restaurant)
    return render_template("restaurants.html", message=message, restaurants=allrestaurants, base_url="http://127.0.0.1:5000/restaurants")

@restaurants.route('/restaurants/<int:restaurant_id>', methods=['POST'])
def create_reservation(restaurant_id):
    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    form = ReservationRequest()
    positive_record = db.session.query(Quarantine).filter(Quarantine.user_id == current_user.id, Quarantine.in_observation == True).first()
    if positive_record is not None:
        return make_response(redirect('/restaurants/'+str(restaurant_id)), 222)
    if form.validate_on_submit():

        #TODO: controllo su data nel passato

        #weekday = form.date.data.weekday() + 1
        reservation_time = time.strptime(request.form['time'], '%H:%M')
        reservation_datetime_str = str(request.form['date']) + " " + str(request.form['time'])
        reservation_datetime = datetime.datetime.strptime(reservation_datetime_str, "%d/%m/%Y %H:%M")
        #reservation_datetime_str = str(reservation_datetime_str) + ' ' + str(reservation_time)
        temp_dict = dict(
            booker_id = current_user.id,
            booker_email = current_user.email,
            restaurant_id = restaurant_id,
            date = str(request.form['date']),
            time = str(request.form['time']),
            places = form.guests.data
        )
        #print(temp_dict)
        res = requests.put(RESERVATION_SERVICE+str('reservations'), json=temp_dict)
        if res.status_code == 200:
            return make_response(render_template('error.html', message="Reservation has been placed", redirect_url="/"), 666)
        else:
            if res.status_code == 400:
                return make_response(render_template('error.html', message="Bad Request", redirect_url="/"), 400)
            elif res.status_code == 500:
                return make_response(render_template('error.html', message="Try again later", redirect_url="/"), 500)
            else:
                return make_response(render_template('error.html', message="Error", redirect_url="/"), 500)

@restaurants.route('/restaurants/<int:restaurant_id>', methods=['GET'])
@login_required
def restaurant_sheet(restaurant_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    cuisinetypes = ""
    for cuisine in restaurantRecord.cuisine_type:
        cuisinetypes = cuisinetypes + cuisine.name + " "

    # get menu
    restaurant_menu = db.session.query(Dish).filter_by(restaurant_id = restaurant_id)


    form = ReservationRequest()

    data_dict = dict(name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    dishes=restaurant_menu,
                                                    restaurant_id=restaurantRecord.id,
                                                    form=form)


    

    return render_template("restaurantsheet.html", **data_dict)


@restaurants.route('/restaurants/delete/<int:restaurant_id>', methods=['GET'])
@login_required
def restaurant_delete(restaurant_id):

    if current_user.role != 'owner':
        return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)

    restaurant = db.session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if restaurant is None:
        return make_response(render_template('error.html', message="Restaurant not found", redirect_url="/"), 404)

    if restaurant.owner_id != current_user.id:
        return make_response(render_template('error.html', message="You are not the restaurant's owner", redirect_url="/"), 403)

    #payload = {'restaurant_name':str(restaurant.name)}
    res = requests.delete('http://localhost:5100/reservations?restaurant_id='+str(restaurant_id)).status_code
    if res == 200:
        print('reservations deleted correctly')
    else:
        print(str(res))

    likes = db.session.query(Like).filter(Like.restaurant_id == restaurant.id).all()
    for like in likes:
        db.session.delete(like)
    reviews = db.session.query(Review).filter(Review.restaurant_id == restaurant.id).all()
    for rev in reviews:
        db.session.delete(rev)
    
    # dishes, working days and tables are deleted on cascade
    db.session.delete(restaurant)
    db.session.commit()

    return make_response(render_template('error.html', message="Restaurant successfully deleted", redirect_url="/"), 200)


@restaurants.route('/restaurants/like/<restaurant_id>')
@login_required
def _like(restaurant_id):

    if (current_user.role == 'owner' or current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    q = Like.query.filter_by(liker_id=current_user.id, restaurant_id=restaurant_id)
    if q.first() == None:
        new_like = Like()
        new_like.liker_id = current_user.id
        new_like.restaurant_id = restaurant_id
        db.session.add(new_like)
        db.session.commit()
        message = ''
    else:
        message = 'You\'ve already liked this place!'
    return _restaurants(message)


@restaurants.route('/restaurants/search', methods=['GET', 'POST'])
@login_required
def search():

    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You can't search for restaurants! Redirecting to home page", redirect_url="/"), 403)

    form = RestaurantSearch()

    if request.method == 'POST':

        if form.validate_on_submit():
            
            cuisine_type_list = []
            for cuisine in form.cuisine_type.data:
                #cuisine_type_list.append(Restaurant.CUISINE_TYPES(cuisine))
                cuisine_type_list.append(cuisine)


            allrestaurants = db.session.query(Restaurant)

            if 'name' in request.form:
                allrestaurants = allrestaurants.filter(Restaurant.name.ilike(r"%{}%".format(request.form['name'])))
            if 'lat' in request.form and request.form['lat'] != '':
                allrestaurants = allrestaurants.filter(Restaurant.lat >= (float(request.form['lat'])-0.1), Restaurant.lat <= (float(request.form['lat'])+0.1))
            if 'lon' in request.form and request.form['lon'] != '':
                allrestaurants = allrestaurants.filter(Restaurant.lon >= (float(request.form['lon'])-0.1), Restaurant.lon <= (float(request.form['lon'])+0.1))
            
            allrestaurants_list = allrestaurants

            if len(cuisine_type_list) >= 1:

                allrestaurants_list = []
                for restaurant in allrestaurants.all():

                    for restaurant_cuisine in restaurant.cuisine_type:
                        
                        if(restaurant_cuisine in cuisine_type_list):
                            allrestaurants_list.append(restaurant)
                            break

            '''
                allrestaurants = allrestaurants.filter(
                    or_(*[Restaurant.cuisine_type == x for x in cuisine_type_list])
                )
            print(allrestaurants)
            #print(request.form['cuisine_type'])
            '''

            return render_template('restaurantsearch.html', form=form, restaurants=allrestaurants_list, restlon=10.4015256, restlat=43.7176589)

    
    return render_template('restaurantsearch.html', form=form)


@restaurants.route('/edit_restaurant_informations', methods=['GET'])
def restaurant_informations_edit():
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

        restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id)
        if restaurants.first() is None:
            return make_response(render_template('error.html', message="You have not restaurants! Redirecting to create a new one", redirect_url="/create_restaurant"), 403)

        # in a GET I list all my restaurants
        return render_template("restaurant_informations_edit.html", restaurants=restaurants)

    # user not logged
    return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


@restaurants.route('/edit_restaurant_informations/<restaurant_id>', methods=['GET','POST'])
def restaurant_edit(restaurant_id):    
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

        record = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).first()
        if record is None:    
            return make_response(
                render_template('error.html', 
                    message="You have not restaurants! Redirecting to create a new one", 
                    redirect_url="/create_restaurant"
                ), 404)


        form = EditRestaurantForm()

        if request.method == 'POST':

            if form.validate_on_submit():

                phone_changed = form.data['phone']

                dishes_changed = []
                dishes_changed = _check_dishes(form.dishes.data)
                del form.dishes

                record.phone = phone_changed
                dishes_to_edit = db.session.query(Dish).filter(Dish.restaurant_id == int(restaurant_id))
                if dishes_to_edit is not None: 
                    for d in dishes_to_edit:
                        db.session.delete(d)

                for el in dishes_changed:
                    newdish = Dish()
                    newdish.restaurant_id = int(restaurant_id)
                    newdish.dish_name = el.dish_name
                    newdish.price = el.price
                    newdish.ingredients = el.ingredients
                    db.session.add(newdish)

                db.session.commit()
                return make_response(render_template('error.html', message="You have correctly edited! Redirecting to your restaurants", redirect_url="/"), 200)

            else:
                # invalid form
                return make_response(render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)
        else: 
            # in the GET we fill all the fields
            form.phone.data = record.phone

            # will not be empty since from the creation of the restaurant at least one dish was added
            dishes_to_edit = db.session.query(Dish).filter(Dish.restaurant_id == int(restaurant_id)).all()
            for idx, d in enumerate(dishes_to_edit):
                if idx > 0:
                    dish_form = DishForm()
                    form.dishes.append_entry(dish_form)
                form.dishes[idx].dish_name.data = d.dish_name
                form.dishes[idx].price.data = d.price
                form.dishes[idx].ingredients.data = d.ingredients

            return render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id)

    # user not logged
    return make_response(
        render_template('error.html', 
            message="You are not logged! Redirecting to login page", 
            redirect_url="/login"
        ), 403)

'''
@restaurants.route('/restaurants/reviews/<restaurant_id>', methods=['GET', 'POST'])
@login_required
def create_review(restaurant_id):
    
    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    reviews = Review.query.filter_by(restaurant_id=int(restaurant_id)).all()

    # get the first resrvation ordered by date
    reservation = Reservation.query.order_by(Reservation.date).filter_by(booker_id = int(current_user.id)).first()

    # the user has not been at restaurant yet
    if (reservation is not None and reservation.date > datetime.datetime.today()):
        reservation = None

    review = Review.query.filter_by(reviewer_id = int(current_user.id)).filter_by(restaurant_id=restaurant_id).first()

    form = ReviewForm()

    if request.method == 'POST':

        if current_user.role == 'owner':
            return make_response(render_template('error.html', message="You are the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

        if reservation is None:
            return make_response(render_template('error.html', message="You have never been at this restaurant! Redirecting to home page", redirect_url="/"), 403)

        if review is not None:
            return make_response(render_template('error.html', message="You have already reviewed this restaurant! Redirecting to home page", redirect_url="/"), 403)

        if form.validate_on_submit():
            # add to database
            new_review = Review()
            new_review.marked = False
            new_review.comment = request.form['comment']
            new_review.rating = request.form['rating']
            new_review.date = datetime.date.today()
            new_review.restaurant_id = restaurant_id
            new_review.reviewer_id = current_user.id
            db.session.add(new_review)
            db.session.commit()
            # after the review don't show the possibility to add another review
            reviews = Review.query.filter_by(restaurant_id=int(restaurant_id)).all()
            #return render_template("reviews_owner.html", reviews=reviews), 200
            return make_response(render_template('error.html', message="Review has been placed", redirect_url="/restaurants/reviews/"+restaurant_id), 200)

        else:
            return render_template("reviews.html", form=form,reviews=reviews), 400


    elif current_user.role == 'customer' and review is None and reservation is not None:
        return render_template("reviews.html", form=form, reviews=reviews), 200

    else:
        return render_template("reviews_owner.html", reviews=reviews), 555
'''
@restaurants.route('/restaurants/reservation_list', methods=['GET'])
@login_required
def reservation_list():

    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)
    
    data_dict = []
    restaurants_records = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    for restaurant in restaurants_records:
        response = requests.get(RESERVATION_SERVICE+'reservations?restaurant_id='+str(restaurant.id))
        if (response.status_code != 200):
            if response.status_code == 500:
                return make_response(render_template('error.html', message="Try it later", redirect_url="/"), 500)
            elif response.status_code == 400:
                return make_response(render_template('error.html', message="Wrong parameters", redirect_url="/"), 400)
            else:
                return make_response(render_template('error.html', message='Error', redirect_url='/'), 500)
        else:
            for reservation in response.json():
                print(reservation)
                booker = db.session.query(User).filter_by(id=reservation['booker_id']).first()
                seat = reservation['seats']
                table = db.session.query(Table).filter_by(restaurant_id=restaurant.id, id=reservation['table_id']).first()
                temp_dict = dict(
                    restaurant_name = restaurant.name,
                    restaurant_id = restaurant.id,
                    date = reservation['date'],
                    table_name = table.table_name,
                    number_of_guests = len(seat),
                    booker_fn = booker.firstname,
                    booker_ln = booker.lastname,
                    booker_phone = booker.phone,
                    reservation_id = reservation['id']
                )
                data_dict.append(temp_dict)
                
    return render_template('restaurant_reservations_list.html', reservations=data_dict)


@restaurants.route('/restaurants/<restaurant_id>/reservation/<reservation_id>', methods=['POST'])
def confirm_participants_post(restaurant_id, reservation_id):
    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()
    #restaurant = requests.get(RESTAURANT_SERVICE+str(restaurant_id)).json
    if (current_user.id != restaurant.owner_id):
        return make_response(render_template('error.html', message="You are not the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

    class ConfirmedSeatFormTest(FlaskForm):
        guests = f.FieldList(f.BooleanField())
        display = ['guests']

    form = ConfirmedSeatFormTest()
    entrances = []
    for key in request.form:
        if key != 'csrf_token':
            email = request.form[key]
            entrances.append(email)
    response = requests.post(RESERVATION_SERVICE+'reservations/'+str(reservation_id)+'/entrances', json=entrances)
    if response.status_code == 200:
        return make_response(render_template('error.html', message="Participants confirmed", redirect_url="/"), 200)
    else:
        if response.status_code == 500:
            return make_response(render_template('error.html', message="Try it later", redirect_url="/restaurants/<restaurant_id>"), 500)
        elif response.status_code == 400:
            return make_response(render_template('error.html', message="Wrong parameters", redirect_url="/restaurants/<restaurant_id>"), 400)
        elif response.status_code == 404:
            return make_response(render_template('error.html', message="Reservation not found", redirect_url="/restaurants/<restaurant_id>"), 400)
        elif response.status_code == 403:
            return make_response(render_template('error.html', message='Reservation is too old or in the future', redirect_url="/restaurants/<restaurant_id>"), 403)
        else:
            return make_response(render_template('error.html', message='Error', redirect_url='/restaurants/<restaurant_id>'), 500)

@restaurants.route('/restaurants/<restaurant_id>/reservation/<reservation_id>', methods=['GET'])
@login_required
def confirm_participants(restaurant_id, reservation_id):
    
    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()
    #restaurant = requests.get(RESTAURANT_SERVICE+str(restaurant_id)).json
    if (current_user.id != restaurant.owner_id):
        return make_response(render_template('error.html', message="You are not the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

    # check if the reservation is in the past or in the future
    response = requests.get(RESERVATION_SERVICE+'reservations/'+str(reservation_id))
    if response.status_code != 200:
        if response.status_code == 500:
            return make_response(render_template('error.html', message="Try it later", redirect_url="/restaurants/<restaurant_id>"), 500)
        elif response.status_code == 400:
            return make_response(render_template('error.html', message="Wrong parameters", redirect_url="/restaurants/<restaurant_id>"), 400)
        elif response.status_code == 404:
            return make_response(render_template('error.html', message="Reservation not found", redirect_url="/restaurants/<restaurant_id>"), 400)
        else:
            return make_response(render_template('error.html', message='Error', redirect_url='/restaurants/<restaurant_id>'), 500)
    else: 
        res = response.json()
        seats = res['seats']

        class ConfirmedSeatFormTest(FlaskForm):
            guests = f.FieldList(f.BooleanField())
            display = ['guests']

        form = ConfirmedSeatFormTest()

        guests = []
        
        for seat in seats:
            #if seat['confirmed'] == True:
                # in this case the participants are already confirmed by the owner
            #    return make_response(render_template('error.html', message="Participants are already confirmed for this reservation", redirect_url="/restaurants/reservation_list"), 403)
            guests.append(seat['guests_email'])

        
            

        return render_template('restaurant_confirm_participants.html', guests=guests, form=form)
