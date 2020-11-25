import json
from flask import Blueprint, redirect, render_template, request, make_response
from database import db_session, User
from auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from forms import (DishForm, UserForm, RestaurantForm, ReservationPeopleEmail, 
                            SubReservationPeopleEmail, ReservationRequest, RestaurantSearch, 
                            EditRestaurantForm, ReviewForm )
from views import auth
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


RESTAURANT_SERVICE = "http://0.0.0.0:5070/"
RESERVATION_SERVICE = 'http://127.0.0.1:5100/'
USER_SERVICE = 'http://127.0.0.1:5060/'
#RESERVATION_SERVICE = os.environ['RESERVATION_SERVICE']
REQUEST_TIMEOUT_SECONDS = 2


def _check_working_days(form_working_days):
    working_days_to_add = []
    
    for wd in form_working_days:
        new_wd = dict()
        str_shifts = '[' + wd['work_shifts'] + ']'
        shifts = list(ast.literal_eval(str_shifts))
        new_wd['work_shifts'] = shifts
        new_wd['day'] = wd['day']

        working_days_to_add.append(new_wd)

    return working_days_to_add


def _check_tables(form_tables):
    tables_to_add = []
    tot_capacity = 0

    for table in form_tables:
        new_table = dict()
        new_table['name'] = table['table_name']
        new_table['capacity'] = table['capacity']

        tot_capacity += new_table['capacity']
        tables_to_add.append(new_table)

    return tables_to_add, tot_capacity


def _check_dishes(form_dishes):
    dishes_to_add = []

    for dish in form_dishes:
        new_dish = dict()
        new_dish['name'] = dish['dish_name']
        new_dish['price'] = dish['price']
        new_dish['ingredients'] = dish['ingredients']

        dishes_to_add.append(new_dish)

    return dishes_to_add

def _compose_url_get_reservations(user_id, restaurant_id, end):
    end_date = end.isoformat()
    url = RESERVATIONS_SERVICE+'reservations'
    url += '?user_id=' + str(user_id) + '&restaurant_id=' + str(restaurant_id) + '&end=' + str(end_date)
    return url


#@restaurants.route('/restaurants/create', methods=['GET'])
def create_restaurant_GET():
    if current_user is not None and hasattr(current_user, 'id'):
        if (current_user.role == 'customer' or current_user.role == 'ha'):
            return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)

        form = RestaurantForm()

        return render_template('create_restaurant.html', form=form)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


#@restaurants.route('/restaurants/create', methods=['POST'])
def create_restaurant_POST():
    if current_user is not None and hasattr(current_user, 'id'):
        if (current_user.role == 'customer' or current_user.role == 'ha'):
            return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)
    
        form = RestaurantForm(request.form)

        if form.validate_on_submit():
            # if one or more fields that must not be present are
            must_not_be_present = ['owner_id', 'capacity', 'tot_reviews', 'avg_rating', 'likes']
            if any(k in must_not_be_present for k in request.form):
                return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

            working_days_to_add = []
            tables_to_add = []
            dishes_to_add = []

            # check that all restaurant/working days/tables/dishes fields are correct
            try:
                working_days_to_add = _check_working_days(form.workingdays.data)
                del form.workingdays

                tables_to_add, tot_capacity = _check_tables(form.tables.data)
                del form.tables

                dishes_to_add = _check_dishes(form.dishes.data)
                del form.dishes

                working_days_to_add_list = []
                for workingday in working_days_to_add:
                    temp_dict = dict()
                    temp_dict['day'] = workingday['day']
                    temp_dict['work_shifts'] = []
                    for shift in workingday['work_shifts']:
                        temp_dict['work_shifts'].append([shift[0],shift[1]])

                    working_days_to_add_list.append(temp_dict)

                restaurant_data = dict(
                    name=form.name.data,
                    lat=form.lat.data,
                    lon=form.lon.data,
                    owner_id=current_user.id,
                    phone=form.phone.data,
                    prec_measures=form.prec_measures.data,
                    avg_time_of_stay=form.avg_time_of_stay.data,
                    cuisine_type=form.cuisine_type.data,
                    dishes=dishes_to_add,
                    tables=tables_to_add,
                    working_days=working_days_to_add_list
                )

                try:

                    reply = requests.put(RESTAURANT_SERVICE+'restaurants', json=restaurant_data, timeout=REQUEST_TIMEOUT_SECONDS)
                    reply_json = reply.json()

                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

                if reply.status_code == 200:
                    return render_template('error.html', message="Restaurant has been created", redirect_url="/")
                else:
                    return render_template('create_restaurant.html', form=form, message=reply_json['detail'])

            except:
                return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

        else:
            # invalid form
            return make_response(render_template('create_restaurant.html', form=form), 400)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


#@restaurants.route('/edit_restaurant/<restaurant_id>', methods=['GET'])
def restaurant_edit_GET(restaurant_id):    
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

        form = EditRestaurantForm()

            # in the GET we fill all the fields
        try:
            reply = requests.get(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
            reply_json = reply.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

        if reply.status_code != 200:
            return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

        if reply_json['owner_id'] != current_user.id:
            return make_response(render_template('error.html', message="You are not the owner of this restaurant", redirect_url="/"), 403)

        form.phone.data = reply_json['phone']

        for idx, d in enumerate(reply_json['dishes']):
            if idx > 0:
                dish_form = DishForm()
                form.dishes.append_entry(dish_form)
            form.dishes[idx].dish_name.data = d['name']
            form.dishes[idx].price.data = d['price']
            form.dishes[idx].ingredients.data = d['ingredients']

        return render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id)

    # user not logged
    else:
        return make_response(
        render_template('error.html', 
            message="You are not logged! Redirecting to login page", 
            redirect_url="/login"
        ), 403)


#@restaurants.route('/edit_restaurant/<restaurant_id>', methods=['POST'])
def restaurant_edit_POST(restaurant_id):  
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)
    
        form = EditRestaurantForm(request.form)

        if form.validate_on_submit():

            dishes_changed = []
            dishes_changed = _check_dishes(form.dishes.data)

            data = dict(
                owner_id=current_user.id,
                phone=form.data['phone'],
                dishes=dishes_changed
            )

            try:

                reply = requests.post(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), json=data, timeout=REQUEST_TIMEOUT_SECONDS)
                reply_json = reply.json()

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

            if reply.status_code != 200:
                return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

            return make_response(render_template('error.html', message="You have correctly edited! Redirecting to your restaurants", redirect_url="/"), 200)

        else:
            # invalid form
            return make_response(render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)


    # user not logged
    else:
        return make_response(
        render_template('error.html', 
            message="You are not logged! Redirecting to login page", 
            redirect_url="/login"
        ), 403)


#@restaurants.route('/restaurants')
@login_required
def _restaurants(message=''):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    
    try:
        reply = requests.get(RESTAURANT_SERVICE+'restaurants', timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if reply.status_code != 200:
        return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

    allrestaurants = []
    for restaurant in reply_json:
        restaurant_dict = dict()
        restaurant_dict['id'] = restaurant['id']
        restaurant_dict['name'] = restaurant['name']
        restaurant_dict['likes'] = restaurant['likes']

        allrestaurants.append(restaurant_dict)

    return render_template("restaurants.html", message=message, restaurants=allrestaurants, base_url="http://127.0.0.1:5000/restaurants")


#@restaurants.route('/restaurants/<int:restaurant_id>', methods=['POST'])
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


#@restaurants.route('/restaurants/<int:restaurant_id>', methods=['GET'])
@login_required
def restaurant_sheet_GET(restaurant_id):

    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    try:
        reply = requests.get(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if reply.status_code != 200:
        return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

    form = ReservationRequest()

    data_dict = dict(
        name=reply_json['name'],
        likes=reply_json['likes'],
        lat=reply_json['lat'],
        lon=reply_json['lon'],
        phone=reply_json['phone'],
        precmeasures=reply_json['prec_measures'],
        cuisinetype=reply_json['cuisine_type'],
        totreviews=reply_json['tot_reviews'],
        avgrating=reply_json['avg_rating'],
        dishes=reply_json['dishes'],
        restaurant_id=restaurant_id,
        form=form
    )    

    return render_template("restaurantsheet.html", **data_dict)
                   

#@restaurants.route('/restaurants/delete/<int:restaurant_id>', methods=['GET'])
@login_required
def restaurant_delete(restaurant_id):

    if current_user.role != 'owner':
        return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)

    try:
        reply = requests.delete(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), json=dict(owner_id=current_user.id), timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if reply.status_code != 200:
        return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

    else:
        return make_response(render_template('error.html', message="Restaurant successfully deleted", redirect_url="/"), 200)


#@restaurants.route('/restaurants/search', methods=['GET'])
@login_required
def search_GET():

    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You can't search for restaurants! Redirecting to home page", redirect_url="/"), 403)

    form = RestaurantSearch()
    
    return render_template('restaurantsearch.html', form=form)


def search_URL_generator(name=None, lat=None, lon=None, cuisine_types=[]):
    url = '/restaurants'
    queries = 0 
    if name is not None:
        if queries == 0:
            url += '?name=' + name.replace(" ", "%")
        else: 
            url += '&name=' + name.replace(" ", "%")
        queries += 1
    if lat is not None:
        if queries == 0:
            url += '?lat=' + str(lat)
        else: 
            url += '&lat=' + str(lat)
        queries += 1
    if lon is not None:
        if queries == 0:
            url += '?lon=' + str(lon)
        else: 
            url += '&lon=' + str(lon)
        queries += 1
    for cuisine in cuisine_types:
        if queries == 0:
            url += '?cuisine_type=' + str(cuisine)
        else: 
            url += '&cuisine_type=' + str(cuisine)
        queries += 1
    return url

#@restaurants.route('/restaurants/search', methods=['POST'])
@login_required
def search_POST():

    # TODO da finire
    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You can't search for restaurants! Redirecting to home page", redirect_url="/"), 403)

    form = RestaurantSearch(request.form)

    if form.validate_on_submit():

        cuisine_type_list = []
        for cuisine in form.cuisine_type.data:
            cuisine_type_list.append(cuisine)

        name = None
        lat = None
        lon = None

        if 'name' in request.form and request.form['name'] != '':
            name = form.name.data
        if 'lat' in request.form and request.form['lat'] != '':
            lat = form.lat.data
        if 'lon' in request.form and request.form['lon'] != '':
            lon = form.lon.data
            
        if lat is None and lon is not None:
            form.lat.errors.append("You must specify lat")
            return render_template('restaurantsearch.html', form=form)
        if lat is not None and lon is None:
            form.lon.errors.append("You must specify lon")
            return render_template('restaurantsearch.html', form=form)

        search_url = search_URL_generator(name,lat,lon,cuisine_type_list)

        try:

            reply = requests.get(RESTAURANT_SERVICE+search_url, timeout=REQUEST_TIMEOUT_SECONDS)
            reply_json = reply.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

        if reply.status_code != 200:
            return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)

        restlat = 43.71
        restlon = 10.40
        if len(reply_json) != 0:
            restlat = reply_json[0]['lat']
            restlon = reply_json[0]['lon']

        return render_template('restaurantsearch.html', form=form, restaurants=reply_json, restlon=restlon, restlat=restlat)
    
    return render_template('restaurantsearch.html', form=form)


#@restaurants.route('/restaurants/like/<restaurant_id>')
@login_required
def _like(restaurant_id):

    if (current_user.role == 'owner' or current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    data = dict(
        restaurant_id=int(restaurant_id),
        user_id=current_user.id
    )

    try:
        reply = requests.put(RESTAURANT_SERVICE+'likes', json=data, timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url=RESTAURANT_SERVICE+"restaurants")

    message = ""

    if reply.status_code == 400:
        message = "An error occured, try again later"
    else:
        if reply.status_code != 200:
            message = reply_json['detail']

    return _restaurants(message)


#@restaurants.route('/restaurants/reviews/<restaurant_id>', methods=['GET'])
@login_required
def create_review_GET(restaurant_id):
    
    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    if current_user.role == 'owner':
        return make_response(render_template('error.html', message="You are the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)


    form = ReviewForm()

    # TODO chiamata verso reservation per verificare se user ha fatto almeno una reservation nel passato
    now = datetime.datetime.now()
    try:
        url = _compose_url_get_reservations(user_id=current_user.id, restaurant_id=restaurant_id, end=now)
        reply = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return connexion.problem(500, "Internal server error", "Reservations service not available")

    # if the user has never been to that restaurant
    reservation_done = False
    if len(reply_json) == 0:
        reservation_done = True


    try:
        review_reply = requests.get(RESTAURANT_SERVICE+'reviews?restaurant_id='+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
        review_reply_json = review_reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url=RESTAURANT_SERVICE+"restaurants")

    reviews = review_reply_json
    user_already_reviewed = False
    for review in reviews:
        if review['user_id'] == current_user.id:
            user_already_reviewed = True
            break


    if current_user.role == 'customer' and user_already_reviewed is False and reservation_done is True:
        return render_template("reviews.html", form=form, reviews=reviews), 200

    else:
        return render_template("reviews_owner.html", reviews=reviews), 555


#@restaurants.route('/restaurants/reviews/<restaurant_id>', methods=['POST'])
@login_required
def create_review(restaurant_id):

    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    if current_user.role == 'owner':
        return make_response(render_template('error.html', message="You are the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

    form = ReviewForm(request.form)

    try:
        review_reply = requests.get(RESTAURANT_SERVICE+'reviews?restaurant_id='+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
        review_reply_json = review_reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url=RESTAURANT_SERVICE+"restaurants")

    if form.validate_on_submit():

        data = dict(
            user_id=current_user.id,
            restaurant_id=restaurant_id,
            rating=request.form['rating'],
            comment=request.form['comment']
        )

        try:
            reply = requests.put(RESTAURANT_SERVICE+'reviews', json=data, timeout=REQUEST_TIMEOUT_SECONDS)
            reply_json = reply.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return render_template('error.html', message="Something gone wrong, try again later", redirect_url=RESTAURANT_SERVICE+"restaurants")


        if reply.status_code == 400:
            message = "An error occured, try again later"
        else:
            if reply.status_code != 200:
                message = reply_json['detail']


    else:
        return make_response(render_template("reviews.html", form=form,reviews=review_reply_json), 400)


#@restaurants.route('/restaurants/reservation_list', methods=['GET'])
@login_required
def reservation_list():

    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)
    
    data_dict = []

    try:

        reply = requests.get(RESTAURANT_SERVICE+'restaurants?owner_id='+str(current_user.id), timeout=REQUEST_TIMEOUT_SECONDS)
        restaurants_records = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    for restaurant in restaurants_records:

        try:
            response = requests.get(RESERVATION_SERVICE+'reservations?restaurant_id='+str(restaurant['id']), timeout=REQUEST_TIMEOUT_SECONDS)
            response_json = response.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")
        
        
        if (response.status_code != 200):
            return make_response(render_template('error.html', message=response_json['detail'], redirect_url='/'), response.status_code)
        else:
            for reservation in response.json():
                
                try:
                    reply = requests.get(USER_SERVICE+'users/'+str(reservation['booker_id']), timeout=REQUEST_TIMEOUT_SECONDS)
                    booker = reply.json()
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")
        
                if (reply.status_code == 200):

                    seat = reservation['seats']
                    tables = restaurant['tables']
                    table_name = ""
                    for table in tables:
                        if table['id'] == reservation['table_id']:
                            table_name = table['name']
                            break

                    temp_dict = dict(
                        restaurant_name = restaurant['name'],
                        restaurant_id = restaurant['id'],
                        date = reservation['date'],
                        table_name = table_name,
                        number_of_guests = reservation['places'],
                        booker_fn = booker['firstname'],
                        booker_ln = booker['lastname'],
                        booker_phone = booker['phone'],
                        reservation_id = reservation['id']
                    )
                    data_dict.append(temp_dict)
                
    return render_template('restaurant_reservations_list.html', reservations=data_dict)


#@restaurants.route('/restaurants/<restaurant_id>/reservation/<reservation_id>', methods=['POST'])
def confirm_participants_post(restaurant_id, reservation_id):
    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

    try:
        reply = requests.get(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
        restaurant = reply.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if (current_user.id != restaurant['owner_id']):
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
    try:
        response = requests.post(RESERVATION_SERVICE+'reservations/'+str(reservation_id)+'/entrances', json=entrances, timeout=REQUEST_TIMEOUT_SECONDS)
        res = response.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if response.status_code == 200:
        return make_response(render_template('error.html', message="Participants confirmed", redirect_url="/restaurants/"+str(restaurant_id)), 200)
    else:
        return make_response(render_template('error.html', message=res['detail'], redirect_url="/restaurants/"+str(restaurant_id)), response.status_code)
       

#@restaurants.route('/restaurants/<restaurant_id>/reservation/<reservation_id>', methods=['GET'])
@login_required
def confirm_participants(restaurant_id, reservation_id):
    
    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

    try:
        reply = requests.get(RESTAURANT_SERVICE+'restaurants/'+str(restaurant_id), timeout=REQUEST_TIMEOUT_SECONDS)
        restaurant = reply.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if (current_user.id != restaurant['owner_id']):
        return make_response(render_template('error.html', message="You are not the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)


    # check if the reservation is in the past or in the future
    try:
        response = requests.get(RESERVATION_SERVICE+'reservations/'+str(reservation_id), timeout=REQUEST_TIMEOUT_SECONDS)
        res = response.json()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    
    if response.status_code != 200:
        return make_response(render_template('error.html', message=res['detail'], redirect_url="/restaurants/<restaurant_id>"), response.status_code)
    else: 
        res = response.json()
        seats = res['seats']

        class ConfirmedSeatFormTest(FlaskForm):
            guests = f.FieldList(f.BooleanField())
            display = ['guests']

        form = ConfirmedSeatFormTest()

        guests = []
        
        for seat in seats:
            guests.append(seat['guests_email'])

        
            
        return render_template('restaurant_confirm_participants.html', guests=guests, form=form)
