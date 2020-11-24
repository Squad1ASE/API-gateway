from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import (db, User, Reservation, Restaurant, Seat,
                               Quarantine, Notification, Like, Review, Table)
from monolith.auth import admin_required
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
from monolith.forms import UserForm, EditUserForm, SubReservationPeopleEmail, EditReservationForm, EmailForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime
from monolith.views.restaurants import restaurant_delete
import requests
import os

import time
from datetime import date
from time import mktime
from datetime import timedelta


users = Blueprint('users', __name__)

RESTAURANT_SERVICE = "http://0.0.0.0:5060/"
#RESERVATION_SERVICE = 'http://127.0.0.1:5100/'
RESERVATION_SERVICE = os.environ['RESERVATION_SERVICE']


@users.route('/users')
@login_required
def _users():
    if (current_user.role != 'admin'):
        return make_response(
            render_template('error.html', message="You are not the admin! Redirecting to home page", redirect_url="/"),
            403)
    users = db.session.query(User)
    return render_template("users.html", users=users)


@users.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(
            render_template('error.html', message="You are already logged! Redirecting to home page", redirect_url="/"),
            403)

    form = UserForm()

    if request.method == 'POST':

        if form.validate_on_submit():

            new_user = User()
            form.populate_obj(new_user)
            new_user.role = request.form['role']
            check_already_register = db.session.query(User).filter(User.email == new_user.email).first()

            if (check_already_register is not None):
                # already registered
                return render_template('create_user.html', form=form), 403

            new_user.set_password(form.password.data)  # pw should be hashed with some salt

            if new_user.role != 'customer' and new_user.role != 'owner':
                return make_response(render_template('error.html',
                                                     message="You can sign in only as customer or owner! Redirecting to home page",
                                                     redirect_url="/"), 403)

            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
        else:
            # invalid form
            return make_response(render_template('create_user.html', form=form), 400)

    return render_template('create_user.html', form=form)


@users.route('/edit_user_informations', methods=['GET', 'POST'])
@login_required
def edit_user():
    form = EditUserForm()
    email = current_user.email
    user = db.session.query(User).filter(User.email == email).first()

    if request.method == 'POST':

        if form.validate_on_submit():

            password = form.data['old_password']

            if (user is not None and user.authenticate(password)):
                user.phone = form.data['phone']
                user.set_password(form.data['new_password'])
                db.session.commit()
                return redirect('/logout')

            else:
                form.old_password.errors.append("Invalid password.")
                return make_response(render_template('edit_user.html', form=form, email=current_user.email), 401)

        else:
            # invalid form
            return make_response(render_template('edit_user.html', form=form, email=current_user.email), 400)

    else:
        form.phone.data = user.phone
        return render_template('edit_user.html', form=form, email=current_user.email)


@users.route('/delete_user', methods=['GET', 'DELETE'])
@login_required
def delete_user():
    if (current_user.role == 'ha'):
        return make_response(render_template('error.html',
                                             message="HA not allowed to sign-out!",
                                             redirect_url="/"), 403)

    user_to_delete = db.session.query(User).filter(User.id == current_user.id).first()

    if user_to_delete.role == 'owner':
        # delete first the restaurant and then treat it as a customer
        restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == user_to_delete.id).all()
        for res in restaurants:
            restaurant_delete(res.id)
    else:
        res = requests.delete('http://localhost:5100/reservations/users/' + str(user_to_delete.id)).status_code
        if res == 200:
            print('user reservations deleted correctly')
        else:
            print(str(res))

    user_to_delete.is_active = False
    db.session.commit()

    return make_response(render_template('error.html',
                                         message="Successfully signed out!",
                                         redirect_url="/logout"), 200)


@users.route('/users/reservation_list', methods=['GET'])
@login_required
def reservation_list():
    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(
            render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"),
            403)
    response = requests.get(RESERVATION_SERVICE+'reservations?user_id=' + str(current_user.id))
    if response.status_code != 200:
        if response.status_code == 500:
            return make_response(render_template('error.html', message="Try it later", redirect_url="/"), 500)
        elif response.status_code == 400:
            return make_response(render_template('error.html', message="Wrong parameters", redirect_url="/"), 400)
        else:
            return make_response(render_template('error.html', message='Error', redirect_url='/'), 500)
    else:
        reservation_records = response.json()
        data_dict=[]
        for reservation in reservation_records:
            temp_dict = dict(
                restaurant_name=db.session.query(Restaurant).filter_by(id = reservation["restaurant_id"]).first().name, #todo endpoint call
                date=reservation["date"],
                reservation_id=reservation["id"]
            )
            data_dict.append(temp_dict)

        return render_template('user_reservations_list.html', reservations=data_dict)


@users.route('/users/deletereservation/<reservation_id>')
@login_required
def deletereservation(reservation_id):
    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(
            render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"),
            403)

    resp = requests.delete(RESERVATION_SERVICE+'reservations/' + str(reservation_id))

    if resp.status_code == 200:
        return reservation_list()
    elif resp.status_code == 404:
        return make_response(
            render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)
    elif resp.status_code == 403:
        return make_response(render_template('error.html', message="You can't delete a past reservation!",
                                             redirect_url="/users/reservation_list"), 403)
    elif resp.status_code == 500:
        return make_response(
            render_template('error.html', message="Try again later", redirect_url="/users/reservation_list"), 500)
    else:
        return make_response(
            render_template('error.html', message="Error", redirect_url="/users/reservation_list"), 500)

@users.route('/users/editreservation/<reservation_id>', methods=['POST'])
def editreservation_post(reservation_id):
    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    form = EditReservationForm()
    if form.validate_on_submit():
        if len(form.data['guest']) + 1 > form.data['places']:
            return make_response(render_template('user_reservation_edit_NUOVA.html', form=form, message='Too much guests!'), 400)

        time_now = datetime.datetime.now().strftime('%H:%M')
        if form.data['date'] < datetime.date.today() or (form.data['date']==datetime.date.today() and str(request.form['time'])<=time_now ):
            return make_response(render_template('user_reservation_edit_NUOVA.html', form=form, message='You cannot edit a past reservertion'), 400)

        d = dict(
            places=form.data['places'],
            seats_email=form.data['guest'],
            booker_email = current_user.email,
            date = str(request.form['date']),
            time = str(request.form['time'])
        )


        data = requests.post(RESERVATION_SERVICE+'reservations/'+str(reservation_id), json=d)
        if data.status_code == 200:                
            # this isn't an error
            return make_response(render_template('error.html', message="Reservation changed!", redirect_url="/"), 200)

        else:
            if data.status_code == 404:
                return make_response(render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)
            elif data.status_code == 500:
                return make_response(render_template('error.html', message="Try it later", redirect_url="/users/reservation_list"), 500)
            elif data.status_code == 400:
                return make_response(render_template('error.html', message="Wrong parameters", redirect_url="/users/reservation_list"), 400)
            else:
                return make_response(render_template('error.html', message='Error', redirect_url='/users/reservation_list'), 500)

    else:
        #invalid form
        return make_response(render_template('user_reservation_edit_NUOVA.html', form=form), 400)

@users.route('/users/editreservation/<reservation_id>', methods=['GET'])
@login_required
def editreservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    response = requests.get(RESERVATION_SERVICE+'reservations/'+str(reservation_id))
    if response.status_code != 200:
        if response.status_code == 404:
            return make_response(render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)
        elif response.status_code == 500:
            return make_response(render_template('error.html', message="Try it later", redirect_url="/users/reservation_list"), 500)
        else:
            return make_response(render_template('error.html', message='Error', redirect_url='/users/reservation_list'), 500)
    else: 
        old_res = response.json()

        seat_query = old_res['seats'] # get all the seats of the reservation (booker and guests if any)      

        for seat in seat_query:
            if seat['guests_email'] == current_user.email:
                seat_query.remove(seat)                 

        form = EditReservationForm()
        
        # in the GET we fill all the fields with the old values
        form['places'].data = old_res['places']

        dt_str = old_res['date']
        dt= datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        print(dt.date(), dt.time())
        form['date'].data = dt.date()
        form['time'].data = dt.time()
        if len(seat_query) > 0:
            for idx, seat in enumerate(seat_query):    
                email_form = EmailForm()
                form.guest.append_entry(email_form)       
                form.guest[idx].guest_email.data = seat['guests_email']

        return render_template('user_reservation_edit_NUOVA.html', form=form, base_url="http://127.0.0.1:5000/users/editreservation/"+reservation_id)

    
 

