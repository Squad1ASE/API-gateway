from flask import Blueprint, redirect, render_template, request, make_response, url_for
from database import db, User, Quarantine, Seat, Reservation, Notification, Restaurant, Table
from auth import admin_required
from forms import GetPatientInformationsForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime
from datetime import timedelta
from sqlalchemy import or_, and_

healthauthority = Blueprint('healthauthority', __name__)


@healthauthority.route('/patient_informations', methods=['GET','POST'])
@login_required
def get_patient_informations():
    if(current_user.role != "ha"):
        return make_response(render_template('error.html', message="Access denied!", redirect_url="/"), 403)

    form = GetPatientInformationsForm()

    if request.method == 'POST':

        if form.validate_on_submit():
            patient = User()
            form.populate_obj(patient)

            getuser = db.session.query(User).filter(User.email == patient.email).first()
            # email isn't correct, user doesn't exist
            if(getuser is None):
                form.email.errors.append("Wrong email. User doesn't exist")
                return render_template('generic_template.html', form=form), 404
                
            elif(getuser.role == 'ha' or getuser.role == 'admin'):
                form.email.errors.append("You can not mark this user!")
                return render_template('generic_template.html', form=form), 403

            # email correct, show patient's informations 
            else:
                getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
                # patient is in observation
                if getuserquarantine_status is not None:
                    startdate = getuserquarantine_status.start_date
                    enddate = getuserquarantine_status.end_date
                    state = "patient already under observation"
                else:
                    startdate = datetime.date.today()
                    enddate = startdate + datetime.timedelta(days=14)
                    state = "patient next under observation"

                return redirect(url_for('.get_patient_informations',    email=getuser.email,
                                                                        firstname=getuser.firstname,
                                                                        lastname=getuser.lastname,
                                                                        dateofbirth=getuser.dateofbirth,
                                                                        state=state,
                                                                        startdate=startdate,
                                                                        enddate=enddate
                                                                        ))
        #getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()
        #getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
        #if request.form['mark_positive_button'] == 'mark_positive' and getuserquarantine_status is None:
        if 'mark_positive_button' in request.form and request.form['mark_positive_button'] == 'mark_positive':
                
            getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()

            startdate = datetime.date.today()
            enddate = startdate + datetime.timedelta(days=14)

            quarantine = Quarantine()
            quarantine.user_id = getuser.id
            quarantine.start_date = startdate
            quarantine.end_date = enddate
            quarantine.in_observation = True

            db.session.add(quarantine)
            db.session.commit()

            # do contact tracing
            _do_contact_tracing(getuser, quarantine.start_date)

            # if the positive is in some future reservation (in the next 14 days) the owners of the restaurants concerned must be notified
            _check_future_reservations(getuser, quarantine.start_date)
                
            # this redirect isn't an error, it display that patient has been successfully marked positive
            return make_response(render_template('error.html', message="Patient marked as positive", redirect_url="/"), 555)     

    if 'go_back_button' in request.form and request.form['go_back_button'] == 'go_back':
        return redirect('/patient_informations')

    if 'email' in request.args:
        getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()
        getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
        
        html = 'patient_informations.html'
        if getuserquarantine_status is not None:
            html = 'patient_informations_nomarkbutton.html'
            
        return render_template(html, email=request.args.get("email"),
                                                            firstname=request.args.get("firstname"),
                                                            lastname=request.args.get("lastname"),
                                                            dateofbirth=request.args.get("dateofbirth"),
                                                            state=request.args.get("state"),
                                                            startdate=request.args.get("startdate"),
                                                            enddate=request.args.get("enddate")
                                                            )


    return render_template('generic_template.html', form=form)



def _do_contact_tracing(positive, start_date):
    # first retrieve the reservations of the last 14 days in which the positive was present
    pre_date = start_date - timedelta(days=14)
    d = {
        'email':positive.email,
        'start_date':start_date
    }
    response = requests.put('http:127.0.0.1:5100/contact_tracing', json=d)
    if response.status_code == 200:
        print(response)
    else:
        print(response)



    '''
    user_reservations = db.session.query(Seat)\
        .join(Reservation, Reservation.id == Seat.reservation_id)\
        .filter(
            Seat.guests_email != None
        )\
        .filter(
            Seat.guests_email == positive.email, 
            Seat.confirmed == True, 
            Reservation.cancelled == False,
            Reservation.date <= start_date,
            Reservation.date >= pre_date
        )\
        .join(Restaurant, Restaurant.id == Reservation.restaurant_id)\
        .join(User, User.id == Restaurant.owner_id)\
        .with_entities(
            Reservation.date, 
            Restaurant.id,
            Restaurant.avg_time_of_stay, 
            User.id,
            User.email
        )\
        .distinct()\

    customers_to_be_notified = set()
    owners_to_be_notified = set()

    # For each reservation where the positive was present, 
    # retrieve all the people in the restaurant who have been in 
    # contact with the positive for at least 15 minutes
    for ur in user_reservations:
        date = ur[0]
        restaurant_id = ur[1]
        avg_time_of_stay = ur[2]
        owner_id = ur[3]
        owner_email = ur[4]

        owners_to_be_notified.add((date, owner_email, owner_id))

        
        //.............(date)..............................................................
                        20:00    20:15                         20:25    20:40
        //________________|--------|*****************************|--------|________________
                                   |                             |  
                                   |------------span-------------|                            
                                   |                             |
        //                 start_contagion_time         end_contagion_time


        // or start at    |______________________________________|         

        // or end at               |______________________________________|
        

        start_contagion_time = date + timedelta(minutes=15)
        span = avg_time_of_stay - 15
        end_contagion_time = date + timedelta(minutes=span)

        users_to_be_notified = db.session.query(Seat)\
            .join(Reservation, Reservation.id == Seat.reservation_id)\
            .filter(
                Seat.guests_email != None, 
                Seat.confirmed == True, 
                Reservation.cancelled == False,
                Reservation.restaurant_id == restaurant_id
            )\
            .filter(
                or_(
                    and_(Reservation.date >= date, Reservation.date <= end_contagion_time),
                    and_(Reservation.date + timedelta(minutes=avg_time_of_stay) >= start_contagion_time, Reservation.date + timedelta(minutes=avg_time_of_stay) <= date + timedelta(minutes=avg_time_of_stay))
                )
            )\
            .with_entities(
                Reservation.date,
                Seat.guests_email,
            )\
            .distinct()

        for u in users_to_be_notified:
            customers_to_be_notified.add(u)


    # create notifications for customers and owners to warn 
    # them that they have been in contact with a positive
    now = datetime.datetime.now()
    for date, email in customers_to_be_notified:
        notification = Notification()
        notification.email = email
        notification.date = now
        notification.type_ = Notification.TYPE(1)
        timestamp = date.strftime("%d/%m/%Y, %H:%M")
        notification.message = 'On ' + timestamp + ' you have been in contact with a positive. Get into quarantine!'

        user = db.session.query(User).filter(User.email == email).first()
        if user is not None:
            notification.user_id = user.id
            notification.email = user.email
            # the positive must not be alerted to have come into contact with itself
            if positive.id == user.id:
                continue

        # check user deleted
        if 'invalid_email' not in notification.email:
            db.session.add(notification)


    for date, email, owner_id in owners_to_be_notified:
        notification = Notification()
        notification.email = email
        notification.date = now
        notification.type_ = Notification.TYPE(1)
        timestamp = date.strftime("%d/%m/%Y, %H:%M")
        notification.message = 'On ' + timestamp + ' there was a positive in your restaurant!'
        notification.user_id = owner_id

        db.session.add(notification)

    db.session.commit()


def _check_future_reservations(positive, start_date):
    # first retrieve the reservations of the last 14 days in which the positive was present
    post_date = start_date + timedelta(days=14)
    user_reservations = db.session.query(Seat)\
        .join(Reservation, Reservation.id == Seat.reservation_id)\
        .filter(
            Seat.guests_email != None
        )\
        .filter(
            Seat.guests_email == positive.email,
            Reservation.cancelled == False,
            Reservation.date >= start_date,
            Reservation.date <= post_date
        )\
        .with_entities(
            Reservation.date, 
            Reservation.booker_id,
            Reservation.restaurant_id,
            Reservation.table_id
        )\
        .all()\

    if len(user_reservations) > 0:
        # create notifications for owners to warnm them
        now = datetime.datetime.now()
        for date, booker_id, restaurant_id, table_id in user_reservations:
            restaurant = db.session.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
            table = db.session.query(Table).filter(Table.id == table_id).first()
            booker = db.session.query(User).filter(User.id == booker_id).first()

            notification = Notification()
            notification.email = restaurant.owner.email
            notification.date = now
            notification.type_ = Notification.TYPE(3)
            
            timestamp = date.strftime("%d/%m/%Y, %H:%M")
            message = 'The reservation of ' + timestamp + ' at table "' + table.table_name + '" of restaurant "' + restaurant.name + '" has a positive among the guests.'
            message = message + ' Contact the booker by email "' + booker.email + '" or by phone ' + booker.phone
            notification.message = message
            notification.user_id = restaurant.owner.id

            db.session.add(notification)

        db.session.commit()
    '''