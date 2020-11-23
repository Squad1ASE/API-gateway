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

users = Blueprint('users', __name__)


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
        # first delete future reservations               
        rs = db.session.query(Reservation).filter(
            Reservation.booker_id == user_to_delete.id,
            Reservation.date >= datetime.datetime.now()).all()
        for r in rs:
            deletereservation(r.id)

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
    reservation_records = requests.get('http://localhost:5100/reservations?user_id=' + str(current_user.id)).json()
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

    resp = requests.delete('http://localhost:5100/reservations/' + str(reservation_id))

    if resp.status_code == 200:
        return reservation_list()
    elif resp.status_code == 403:
        return make_response(render_template('error.html', message="You can't delete a past reservation!",
                                             redirect_url="/users/reservation_list"), 403)
    else:
        return make_response(
            render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)


@users.route('/users/editreservation/<reservation_id>', methods=['GET','POST'])
@login_required
def editreservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    old_res = requests.get('http://localhost:5100/reservations/'+str(reservation_id)).json()        

    if old_res:
        seat_query = old_res['seats'] # get all the seats of the reservation (booker and guests if any)      

        #for seat in seat_query:
        #    if seat['guests_email'] == current_user.email:
        #        seat_query.remove(seat)                    


        form = EditReservationForm()
        if request.method == 'POST':
            if form.validate_on_submit():                

                """
                places_changed = form.data['places'] 
                # value >=1 is checked through form validate()

                # correct email values are checked through form validate()

                print('I have the following new emails', form.data['guest'])
                for g in form.data['guest']:
                    print('each email:', g)
                """

                d = dict(
                    places=form.data['places'],
                    seats_email=form.data['guest'],
                    booker_email = current_user.email
                )

                data = requests.post('http://localhost:5100/reservations/'+str(reservation_id), json=d)
                if data.status_code == 200:                
                    # this isn't an error
                    return make_response(render_template('error.html', message="Reservation changed!", redirect_url="/"), 200)

                else:
                    return make_response(render_template('error.html', message="Reservation NOT changed!", redirect_url="/"), 200)


            else:
                #invalid form
                return make_response(render_template('user_reservation_edit_NUOVA.html', form=form, base_url="http://127.0.0.1:5000/users/editreservation/"+reservation_id), 400)


        else:
            # in the GET we fill all the fields with the old values
            form['places'].data = old_res['places']    

            for idx, seat in enumerate(seat_query):                
                if idx > 0:
                    email_form = EmailForm()
                    form.guest.append_entry(email_form)                
                form.guest[idx].guest_email.data = seat['guests_email']

            return render_template('user_reservation_edit_NUOVA.html', form=form, base_url="http://127.0.0.1:5000/users/editreservation/"+reservation_id)
    
 
    else:
        return make_response(render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)

