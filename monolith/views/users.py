from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import ( db, User, Quarantine, Notification)
from monolith.auth import admin_required
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
from monolith.forms import UserForm, EditUserForm, SubReservationPeopleEmail, EditReservationForm, EmailForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime
import os
import time
from datetime import date
from time import mktime
from datetime import timedelta
import json
from monolith.json_converter import user_to_json
import requests

users = Blueprint('users', __name__)

USER_SERVICE = 'http://127.0.0.1:5070/'
RESERVATION_SERVICE = 'http://127.0.0.1:5100/'
#RESERVATION_SERVICE = os.environ['RESERVATION_SERVICE']
REQUEST_TIMEOUT_SECONDS = 2

@users.route('/users')
@login_required
def _users():
    if (current_user.role != 'admin'):
        return make_response(render_template('error.html', message="You are not the admin! Redirecting to home page", redirect_url="/"), 403)
    
    try:
        reply = requests.get(USER_SERVICE+'users', timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if reply.status_code == 200:
        return render_template("users.html", users=reply_json)
    else:
        return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)


@users.route('/users/create', methods=['GET'])
def create_user_GET():
    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(
            render_template('error.html', message="You are already logged! Redirecting to home page", redirect_url="/"),
            403)

    form = UserForm()

    return render_template('create_user.html', form=form)

@users.route('/users/create', methods=['POST'])
def create_user_POST():

    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(render_template('error.html', message="You are already logged! Redirecting to home page", redirect_url="/"), 403)

    form = UserForm(request.form)

    if form.validate_on_submit():
            
        user = user_to_json(request.form.to_dict())

        try:
            reply = requests.put(USER_SERVICE+'users', json=user, timeout=REQUEST_TIMEOUT_SECONDS)
            reply_json = reply.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

        if reply.status_code == 200:
            return render_template('error.html', message="User has been created", redirect_url="/")
        else:
            return make_response(render_template('create_user.html', form=form, message=reply_json['detail']), reply.status_code)
    else:
        # invalid form
        return make_response(render_template('create_user.html', form=form), 400)


@users.route('/users/edit', methods=['GET'])
@login_required
def edit_user_GET():

    form = EditUserForm()

    form.phone.data = current_user.phone
    return render_template('edit_user.html', form=form, email=current_user.email)

@users.route('/users/edit', methods=['POST'])
@login_required
def edit_user_POST():

    if current_user is None:
        return make_response(render_template('error.html', message="You must be logged first! Redirecting to home page", redirect_url="/"), 403)

    form = EditUserForm(request.form)

    if form.validate_on_submit():

        edit_dict = dict(
            current_user_email=current_user.email,
            current_user_old_password=form.data['old_password'],
            current_user_new_password=form.data['new_password'],
            user_new_phone=form.data['phone']
        )
                
        if(edit_dict['user_new_phone'] == current_user.phone and form.data['old_password'] == form.data['new_password']):
            return redirect('/')

        try:
            reply = requests.post(USER_SERVICE+'users', json=edit_dict, timeout=REQUEST_TIMEOUT_SECONDS)
            reply_json = reply.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

        if reply.status_code == 200:
            current_user.phone = edit_dict['user_new_phone']
            db.session.commit()
            return render_template('error.html', message="The information has been updated", redirect_url="/")
        else:
            form.old_password.errors.append(reply_json['detail'])
            return make_response(render_template('edit_user.html', form=form, email=current_user.email), reply.status_code)

    else:
        # invalid form
        return make_response(render_template('edit_user.html', form=form, email=current_user.email), 400)


@users.route('/users/delete', methods=['GET'])
@login_required
def delete_user():

    data = dict(current_user_email=current_user.email)

    try:
        reply = requests.delete(USER_SERVICE+'users', json=data, timeout=REQUEST_TIMEOUT_SECONDS)
        reply_json = reply.json()

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        return render_template('error.html', message="Something gone wrong, try again later", redirect_url="/")

    if reply.status_code == 200:
        return render_template('error.html', message="You account is going to be deleted", redirect_url="/logout")
    else:
        return make_response(render_template('error.html', message=reply_json['detail'], redirect_url="/"), reply.status_code)


@users.route('/users/reservation', methods=['GET'])
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

        return render_template('user_reservation_edit_NUOVA.html', form=form)

    
 

