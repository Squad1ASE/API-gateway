from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import ( db, User, Reservation, Restaurant, Seat,
                                Quarantine, Notification, Like, Review, Table)
from monolith.auth import admin_required
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
from monolith.forms import UserForm, EditUserForm, SubReservationPeopleEmail
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
        return make_response(render_template('error.html', message="You are not the admin! Redirecting to home page", redirect_url="/"), 403)
    users = db.session.query(User)
    return render_template("users.html", users=users)


@users.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(render_template('error.html', message="You are already logged! Redirecting to home page", redirect_url="/"), 403)

    form = UserForm()

    if request.method == 'POST':

        if form.validate_on_submit():

            new_user = User()
            form.populate_obj(new_user)
            new_user.role = request.form['role']
            check_already_register = db.session.query(User).filter(User.email == new_user.email).first()
            
            if(check_already_register is not None):
                # already registered
                return render_template('create_user.html', form=form), 403
                
            new_user.set_password(form.password.data) #pw should be hashed with some salt
            
            if new_user.role != 'customer' and new_user.role != 'owner':
                return make_response(render_template('error.html', message="You can sign in only as customer or owner! Redirecting to home page", redirect_url="/"), 403)
            
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


@users.route('/delete_user', methods=['GET','DELETE'])
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
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    
    '''
    reservation_records = db.session.query(Reservation).filter(
        Reservation.booker_id == current_user.id, 
        Reservation.cancelled == False,
        Reservation.date >= datetime.datetime.now()
    ).all()

    data_dict = []
    for reservation in reservation_records:
        rest_name = db.session.query(Restaurant).filter_by(id = reservation.restaurant_id).first().name
        temp_dict = dict(
            restaurant_name = rest_name,
            date = reservation.date,
            reservation_id = reservation.id
        )
        data_dict.append(temp_dict)
    '''
    data_dict = requests.get('http://localhost:5100/reservations/users/'+str(current_user.id)).json()

    return render_template('user_reservations_list.html', reservations=data_dict)


@users.route('/users/deletereservation/<reservation_id>')
@login_required
def deletereservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)


    reservation = db.session.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.booker_id == current_user.id
    ).first()

    if reservation is not None:
        now = datetime.datetime.now()
        if reservation.date < now:
            return make_response(render_template('error.html', message="You can't delete a past reservation!", redirect_url="/users/reservation_list"), 403)

        seat_query = Seat.query.filter_by(reservation_id = reservation.id).all()

        for seat in seat_query:
            seat.confirmed = False

        reservation.cancelled = True

        table = db.session.query(Table).filter(Table.id == reservation.table_id).first()
        restaurant = db.session.query(Restaurant).filter(Restaurant.id == reservation.restaurant_id).first()
        restaurant_owner = db.session.query(User).filter(User.id == restaurant.owner_id).first()

        
        notification = Notification()
        notification.email = restaurant_owner.email
        notification.date = now
        notification.type_ = Notification.TYPE(2)
        notification.message = 'The reservation of the ' + table.table_name + ' table for the date ' + str(reservation.date) + ' has been canceled'
        notification.user_id = restaurant_owner.id

        db.session.add(notification)

        db.session.commit()
        return reservation_list()

    return make_response(render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)


@users.route('/users/editreservation/<reservation_id>', methods=['GET','POST'])
@login_required
def editreservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    q = db.session.query(Reservation).filter(Reservation.id == reservation_id, Reservation.booker_id == current_user.id).first()
    
    if q is not None:

        seat_query = db.session.query(Seat).filter(Seat.reservation_id == q.id, Seat.guests_email != current_user.email).order_by(Seat.id).all()
        table = db.session.query(Table).filter(Table.id == q.table_id).first()   

        guests_email_list = list()

        for seat in seat_query:
            guests_email_list.append(seat.guests_email)

        class ReservationForm(FlaskForm):
            pass

        guests_field_list = []
        for idx in range(table.capacity-1):
            setattr(ReservationForm, 'guest'+str(idx+1), f.StringField('guest '+str(idx+1)+ ' email'))
            guests_field_list.append('guest'+str(idx+1))

        setattr(ReservationForm, 'display', guests_field_list)

        form = ReservationForm()
            
        if request.method == 'POST':

            if form.validate_on_submit():

                for idx, emailField in enumerate(guests_field_list):                        
                    # checking if already inserted guests email have been changed
                    if(idx < len(guests_email_list)):
                        if(form[emailField].data != guests_email_list[idx]):
                            if not form[emailField].data:
                                db.session.delete(seat_query[idx]) 
                            else:
                                seat_query[idx].guests_email = form[emailField].data
                        
                        db.session.commit()

                    # checking if customer added new guests (if seats available)
                    else:
                        if form[emailField].data != "":
                            seat = Seat()
                            seat.reservation_id = reservation_id
                            seat.guests_email = form[emailField].data
                            seat.confirmed = False
                                
                            db.session.add(seat)
                        
                            db.session.commit()

                # this isn't an error
                return make_response(render_template('error.html', message="Guests changed!", redirect_url="/"), 222)

        if(len(guests_email_list) >= 1):
            for idx, guestemail in enumerate(guests_email_list):
                form[guests_field_list[idx]].data = guestemail

        return render_template('user_reservation_edit.html', form=form)
    
    else:
        return make_response(render_template('error.html', message="Reservation not found", redirect_url="/users/reservation_list"), 404)

    
    






