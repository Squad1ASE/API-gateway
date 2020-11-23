import datetime
import json

import connexion, logging
from reservation import database
import requests
from celery import Celery
from flask import jsonify

from reservation.database import db_session, Reservation, Seat

logging.basicConfig(level=logging.INFO)
database.init_db()
app = connexion.App(__name__, specification_dir='static/')
app.add_api('swagger.yml')

# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
application = app.app


def create_app():
    logging.basicConfig(level=logging.INFO)
    app = connexion.App(__name__, specification_dir='static/')
    app.add_api('swagger.yml')
    database.init_db()
    return app

# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
app = create_app()
application = app.app

def make_celery(app):
    celery = Celery(
        app.import_name,
        # broker=os.environ['CELERY_BROKER_URL'],
        # backend=os.environ['CELERY_BACKEND_URL']
        backend='redis://localhost:6379',
        broker='redis://localhost:6379'
    )
    celery.conf.update(app.config)
    celery.conf.beat_schedule = {'hello': {
        'task': 'app.hello',
        'schedule': 5
    }, 'delete_reservations_task': {
        'task': 'app.delete_reservations_task',
        'schedule': 5
    }
    }
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(application)

@celery.task()
def hello():
    print('Celery is working!')

@celery.task()
def delete_reservations_task():

    reservations=db_session.query(Reservation).filter(Reservation.cancelled != None).all()
    for reservation in reservations:
        notification = {}
        tipo = reservation.cancelled.split()

        if tipo[0]=='reservation_deleted':
            restaurant_owner_id = tipo[1]
            table_name=""
            for item in tipo[2:]:
                table_name=table_name+' '+item

            notification = {
                "type":2,
                "message":'The reservation of the ' + table_name + ' table for the date ' + str(
                    reservation.date) + ' has been canceled',
                "user_id":restaurant_owner_id
            }

        elif tipo[0] == 'user_deleted':
            db_session.delete(reservation)
            db_session.commit()
            print('deleted reservation, motivation: '+tipo[0])
            continue

        elif tipo[0] == 'restaurant_deleted':
            restaurant_name = ""
            for item in tipo[1:]:
                restaurant_name=restaurant_name+' '+item
            print(restaurant_name+'----------------------')
            timestamp = reservation.date
            booker_id = reservation.booker_id

            notification = {
                "type": 2,
                "message": 'Your reservation of ' + str(
                    timestamp) + ' at restaurant ' + restaurant_name + ' has been canceled due to the restaurant closing',
                "user_id": int(booker_id)
            }

        res = requests.put('http://127.0.0.1:5000/users/notification', json=json.dumps(notification))
        # se fallisce verrà ripescata da celery al prossimo giro
        if res.status_code == 200:
            print('deleted reservation, motivation: ' + tipo[0])
            db_session.delete(reservation)
            db_session.commit()


    return


@application.teardown_appcontext
def shutdown_session(exception=None):
    database.db_session.remove()


if __name__ == '__main__':
    app.run(port=5100)
