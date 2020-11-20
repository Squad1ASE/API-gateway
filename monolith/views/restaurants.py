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

restaurants = Blueprint('restaurants', __name__)


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


@restaurants.route('/restaurants/<int:restaurant_id>', methods=['GET','POST'])
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


    if request.method == 'POST':
                positive_record = db.session.query(Quarantine).filter(Quarantine.user_id == current_user.id, Quarantine.in_observation == True).first()
                if positive_record is not None:
                    return make_response(redirect('/restaurants/'+str(restaurant_id)), 222)
                if form.validate_on_submit():

                    #weekday = form.date.data.weekday() + 1
                    reservation_time = time.strptime(request.form['time'], '%H:%M')
                    reservation_datetime_str = str(request.form['date']) + " " + str(request.form['time'])
                    reservation_datetime = datetime.datetime.strptime(reservation_datetime_str, "%d/%m/%Y %H:%M")
                    #reservation_datetime_str = str(reservation_datetime_str) + ' ' + str(reservation_time)
                    temp_dict = dict(
                        booker_id = current_user.id,
                        booker_email = current_user.email,
                        restaurant_id = restaurant_id,
                        #date = datetime.datetime.strftime(reservation_datetime),
                        date = str(request.form['date']),
                        time = str(request.form['time']),
                        places = form.guests.data
                    )
                    print(temp_dict)
                    if requests.put('http://127.0.0.1:5100/reservations/users/'+str(current_user.id), json=temp_dict).status_code == 200:
                        return make_response(render_template('error.html', message="Reservation has been placed", redirect_url="/"), 666)
                    else:
                        return make_response(render_template('error.html', message="Error", redirect_url="/"), 403)

                    '''
                    tavoli = db.session.query(Table).filter(Table.restaurant_id == restaurant_id).all()
                    # 1 transform datetime from form in week day
                    # 2 search inside working day DB with restaurant ID, check if in the specific day and time the restaurant is open
                    # 3 check the list of available tables, the search starts from reservation (consider avg_stay_time)
                    # 4 check in the remaining tables if there is at least one that has more or equals seats then the required
                    
                    # if customer is under observation (positive), reservation is denied

                    positive_record = db.session.query(Quarantine).filter(Quarantine.user_id == current_user.id, Quarantine.in_observation == True).first()
                    if positive_record is not None:
                        return make_response(render_template('restaurantsheet.html', **data_dict, state_message="You are under observation! Reservations are denied"), 222)

                    weekday = form.date.data.weekday() + 1
                    workingday = db.session.query(WorkingDay).filter(WorkingDay.restaurant_id == int(restaurant_id)).filter(WorkingDay.day == WorkingDay.WEEK_DAYS(weekday)).first()
                    
                    if workingday is None:
                        return make_response(render_template('restaurantsheet.html', **data_dict, state_message="Restaurant isn't open this day"), 333)
                    
                    time_span = False
                    reservation_time = time.strptime(request.form['time'], '%H:%M')
                    for shift in workingday.work_shifts:
                        try:
                            start = time.strptime(shift[0], '%H:%M')
                            end = time.strptime(shift[1], '%H:%M')
                            if reservation_time >= start and reservation_time <= end:
                                time_span = True
                                break
                        except:
                            print("except")

                    if time_span is False:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="Restaurant isn't open at this hour"), 444)

                    table_records = db.session.query(Table).filter(
                            Table.restaurant_id == int(restaurant_id),
                            Table.capacity >= form.guests.data
                        ).all()

                    if len(table_records) == 0:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="There are no table with this capacity"), 555)

                    reservation_datetime_str = str(request.form['date']) + " " + str(request.form['time'])
                    reservation_datetime = datetime.datetime.strptime(reservation_datetime_str, "%d/%m/%Y %H:%M")

                    start_reservation = reservation_datetime - timedelta(minutes=restaurantRecord.avg_time_of_stay)
                    end_reservation = reservation_datetime + timedelta(minutes=restaurantRecord.avg_time_of_stay)

    
                    reserved_table_records = db.session.query(Reservation).filter(
                            Reservation.date >= start_reservation,
                            Reservation.date <= end_reservation,
                            Reservation.cancelled == False
                        ).all()

                    #reserved_table_id = reserved_table_records.values('table_id')
                    reserved_table_id = [reservation.table_id for reservation in reserved_table_records]
                    table_records.sort(key=lambda x: x.capacity)

                    table_id_reservation = None
                    for table in table_records:
                        if table.id not in reserved_table_id:
                            table_id_reservation = table.id
                            break


                    if table_id_reservation is None:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="No table available for this amount of people at this time"), 404)
                    else:
                        return redirect('/restaurants/'+str(restaurant_id)+'/reservation?table_id='+str(table_id_reservation)+'&'+'guests='+str(form.guests.data)+'&'+'date='+reservation_datetime_str)
                        #return redirect('/restaurants/'+str(restaurant_id)+'/reservation', table_id=table_id_reservation, guests=form.guests.data)
                '''

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

    now = datetime.datetime.now()
    reservations = db.session.query(Reservation).filter(
        Reservation.date >= now, 
        Reservation.restaurant_id == restaurant.id,
        Reservation.cancelled == False
        ).all()
    if len(reservations) > 0:
        for res in reservations:
            notification = Notification()
            notification.email = res.booker.email
            notification.date = now
            notification.type_ = Notification.TYPE(2)
            timestamp = res.date.strftime("%d/%m/%Y, %H:%M")
            notification.message = 'Your reservation of ' + timestamp + ' at restaurant ' + restaurant.name + ' has been canceled due to the restaurant closing'
            notification.user_id = res.booker.id
            db.session.add(notification)
            res.cancelled = True
        db.session.commit()

    reservations = db.session.query(Reservation).filter(Reservation.restaurant_id == restaurant.id).all()
    for res in reservations:
        db.session.delete(res)
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


@restaurants.route('/restaurants/<int:restaurant_id>/reservation', methods=['GET','POST'])
@login_required
def reservation(restaurant_id):
  
    if (current_user.role == 'owner' or current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)



    positive_record = db.session.query(Quarantine).filter(Quarantine.user_id == current_user.id, Quarantine.in_observation == True).first()
    if positive_record is not None:
        return make_response(redirect('/restaurants/'+str(restaurant_id)), 222)

    table_id = int(request.args.get('table_id'))

    # minus 1 because one is the user placing the reservation
    guests = int(request.args.get('guests')) -1
    date = datetime.datetime.strptime(request.args.get('date'), "%d/%m/%Y %H:%M")

        
    class ReservationForm(FlaskForm):
        pass

    guests_field_list = []
    for idx in range(guests):
        setattr(ReservationForm, 'guest'+str(idx+1), f.StringField('guest '+str(idx+1)+ ' email', validators=[Length(10, 64), Email()]))
        guests_field_list.append('guest'+str(idx+1))

    setattr(ReservationForm, 'display', guests_field_list)

    form = ReservationForm()

    if request.method == 'POST':

            if form.validate_on_submit():



                reservation = Reservation()
                reservation.booker_id = current_user.id
                reservation.restaurant_id = restaurant_id
                reservation.table_id = table_id
                reservation.date = date
                reservation.cancelled = False

                #this prevents concurrent reservations
                check_reservation = db.session.query(Reservation).filter(
                            Reservation.date == reservation.date,
                            Reservation.table_id == reservation.table_id,
                            Reservation.restaurant_id == reservation.restaurant_id,
                            Reservation.cancelled == False
                        ).first()

                if check_reservation is not None:
                    return render_template('error.html', message="Ops someone already placed a reservation", redirect_url='/restaurants/'+str(restaurant_id))


                db.session.add(reservation)
                db.session.commit()
                for emailField in guests_field_list:
                    
                    seat = Seat()
                    seat.reservation_id = reservation.id
                    seat.guests_email = form[emailField].data
                    seat.confirmed = False
                    
                    db.session.add(seat)
                    
                # seat of the booker
                seat = Seat()
                seat.reservation_id = reservation.id
                seat.guests_email = current_user.email
                seat.confirmed = False

                db.session.add(seat)
                db.session.commit()

                # this isn't an error
                return make_response(render_template('error.html', message="Reservation has been placed", redirect_url="/"), 666)
                
    return render_template('reservation.html', form=form)


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

@restaurants.route('/restaurants/reservation_list', methods=['GET'])
@login_required
def reservation_list():

    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)
    
    
    data_dict = []
    restaurants_records = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()
    '''
    for restaurant in restaurants_records:
        
        reservation_records = db.session.query(Reservation).filter(
            Reservation.restaurant_id == restaurant.id, 
            Reservation.cancelled == False,
            Reservation.date >= datetime.datetime.now() - timedelta(hours=3)
        ).all()
    '''
    for restaurant in restaurants_records:
        for reservation in requests.get('http://localhost:5100/reservations/restaurants/'+str(restaurant.id)).json():
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

    '''

        for reservation in reservation_records:
            booker = db.session.query(User).filter(User.id == reservation.booker_id).first()
            seat = db.session.query(Seat).filter(Seat.reservation_id == reservation.id).all()
            table = db.session.query(Table).filter(Table.id == reservation.table_id).first()
            temp_dict = dict(
                restaurant_name = restaurant.name,
                restaurant_id = restaurant.id,
                date = reservation.date,
                table_name = table.table_name,
                number_of_guests = len(seat),
                booker_fn = booker.firstname,
                booker_ln = booker.lastname,
                booker_phone = booker.phone,
                reservation_id = reservation.id
            )
            data_dict.append(temp_dict)

    data_dict = sorted(data_dict, key = lambda i: (i['restaurant_name'],i['date']))
    '''
    
    
                
    return render_template('restaurant_reservations_list.html', reservations=data_dict)


@restaurants.route('/restaurants/<restaurant_id>/reservation/<reservation_id>', methods=['GET', 'POST'])
@login_required
def confirm_participants(restaurant_id, reservation_id):
    
    if (current_user.role == 'ha' or current_user.role == 'customer'):
        return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

    restaurant = db.session.query(Restaurant).filter_by(id=restaurant_id).first()
    if (current_user.id != restaurant.owner_id):
        return make_response(render_template('error.html', message="You are not the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

    # check if the reservation is in the past or in the future
    '''
    reservation = db.session.query(Reservation).filter_by(id=reservation_id).first()
    if (reservation is None or reservation.date <= datetime.datetime.now() - timedelta(hours=3) or reservation.date >= datetime.datetime.now()):
        return make_response(render_template('error.html', message="You can't confirm participants for this reservation!", redirect_url="/restaurants/reservation_list"), 403)

    # get the guests in this reservation

    seats = db.session.query(Seat).filter_by(reservation_id=reservation_id).all()
    '''
    seats = requests.get('http://127.0.0.1:5100/reservations/'+str(reservation_id)+'/seats').json()

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

    if request.method == 'POST':
        '''
        
        # get all the confirmed participants
        for key in request.form:
            if key != 'csrf_token':
                email = request.form[key]
                seat = db.session.query(Seat).filter_by(guests_email=email).filter_by(reservation_id=reservation_id).first()
                seat.confirmed = True
                db.session.commit()
        '''
        entrances = []
        for key in request.form:
            if key != 'csrf_token':
                email = request.form[key]
                entrances.append(email)
        if requests.post('http://127.0.0.1:5100/reservations/'+str(reservation_id)+'/entrances', json=entrances).status_code == 200:
            #TODO: maybe create an apposite page that lists all confirmed participants
            return make_response(render_template('error.html', message="Participants confirmed", redirect_url="/"), 200)
        else:
            return make_response(render_template('error.html', message="Error", redirect_url="/"), 403)
        

    return render_template('restaurant_confirm_participants.html', guests=guests, form=form)
