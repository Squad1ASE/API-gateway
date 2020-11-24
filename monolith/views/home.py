from flask import Blueprint, render_template, redirect
from monolith.database import db, Notification, User
from monolith.auth import current_user
import datetime
from datetime import timedelta
import requests

home = Blueprint('home', __name__)

RESTAURANT_SERVICE = "http://0.0.0.0:5060/"

@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        
        if current_user.role == 'admin':
            restaurants = db.session.query(Restaurant)
            return render_template("homepage_info.html", restaurants=restaurants)


        if current_user.role == 'ha':
            date_of_interest = datetime.date.today() - datetime.timedelta(days=14)
            possible_infected = db.session.query(Notification)\
                .filter(Notification.date > date_of_interest, Notification.type_ == Notification.TYPE(1))\
                .all()
            
            dict_possible_infected = dict() 
            for pi in possible_infected:
                # TODO: per monolith ok recuperare la data dal messaggio. Per lo splitting
                # forse sarà necessario introdurre una data aggiuntiva alle notifiche
                # che rappresenti la data di contatto (il field 'data' in Notification fa riferimento 
                # all data di creazione della notifica, non al contatto)
                contact_date = _retrieve_date(pi.message)
                if pi.email not in dict_possible_infected:
                    new = None
                    if pi.user_id is not None:
                        user = db.session.query(User).filter(User.id == pi.user_id).first()
                        if user is not None:
                            if user.role == 'customer':
                                new = dict(date=contact_date, email=pi.email, phone=user.phone, firstname=user.firstname, lastname=user.lastname)
                            else:
                                continue
                        else:
                            new = dict(date=contact_date, email=pi.email, phone='', firstname='', lastname='')
                    else:
                        new = dict(date=contact_date, email=pi.email, phone='', firstname='', lastname='')
                    dict_possible_infected[pi.email] = new
                else:
                    if contact_date > dict_possible_infected[pi.email]['date']:
                        dict_possible_infected[pi.email]['date'] = contact_date

            possible_infected_sorted = dict() 
            if dict_possible_infected:
                possible_infected_not_sorted = dict_possible_infected.values()
                possible_infected_sorted = sorted(possible_infected_not_sorted, key=lambda k: k['date']) 
            return render_template("homepage_info.html", possible_infected=possible_infected_sorted) 

          
        if current_user.role == 'customer':
            notifications = db.session.query(Notification).filter(Notification.user_id == current_user.id).all()
            return render_template("homepage_info.html", notifications=notifications)


        if current_user.role == 'owner':

            reply = requests.get(RESTAURANT_SERVICE+'restaurants?owner_id='+str(current_user.id))
            reply_json = reply.json()

            return render_template("homepage_info.html", restaurants=reply_json) 
    else:
        return render_template("homepage.html") 


def _retrieve_date(message):
    start = message.find('/') - 2
    end = message.rfind('/') + 4 + 1
    date_str = message[start:end]
    return datetime.datetime.strptime(date_str, '%d/%m/%Y')
