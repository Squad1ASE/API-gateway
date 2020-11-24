import os
from flask import Flask
from database import ( db, User, Restaurant, Table, WorkingDay,
                                Reservation, Like, Seat, Review, 
                                Dish, Quarantine, Notification )
from views import blueprints
from auth import login_manager
from monolith.utilities import ( insert_ha, create_user_EP, user_login_EP, 
                                user_logout_EP, create_restaurant_EP, customers_example, 
                                restaurant_example, admin_example, health_authority_example, 
                                restaurant_owner_example )
import datetime
from datetime import timedelta, date

import time
from celery import Celery
from flask_mail import Message, Mail


        
def create_app():
    app = Flask(__name__)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URI']
    #app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gooutsafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    
    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'gooutsafe1@gmail.com'
    app.config['MAIL_PASSWORD'] = 'Admin123.'
    app.config['MAIL_DEFAULT_SENDER'] = 'gooutsafe@gmail.com'
    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    db.init_app(app)
    login_manager.init_app(app)
    try:
        db.create_all(app=app)
    except Exception as e:
        print(e)


    # TODO THIS SECTION MUST BE REMOVED, ONLY FOR DEMO
    # already tested EndPoints are used to create examples
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        
        q = db.session.query(User).filter(User.email == 'admin@admin.com')
        adm = q.first()
        if adm is None:
            try: 
                # create a first admin user 
                # test for a user defined in database.db
                example = User()
                example.email = 'admin@admin.com'
                example.phone = '3333333333'
                example.firstname = 'Admin'
                example.lastname = 'Admin'
                example.set_password('admin')
                example.dateofbirth = datetime.date(2020, 10, 5)
                example.role = 'admin'           
                example.is_admin = True
                db.session.add(example)
                db.session.commit()

        

                test_client = app.test_client()

                insert_ha(db, app)
                
                for user in customers_example:
                    create_user_EP(test_client,**user)

                for user in restaurant_owner_example:
                    create_user_EP(test_client,**user)

                for usr_idx,restaurant in enumerate(restaurant_example):
                    user_login_EP(test_client, restaurant_owner_example[usr_idx]['email'], 
                                                restaurant_owner_example[usr_idx]['password'])

                    create_restaurant_EP(test_client,restaurant)

                    user_logout_EP(test_client)
                user_logout_EP(test_client)

            except Exception as e:
                print(e)

        

    app.config['WTF_CSRF_ENABLED'] = True

    

    return app


    app=create_app()

    if __name__ == '__main__':
        app.run(host='0.0.0.0')
