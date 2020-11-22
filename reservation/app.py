import connexion, logging
from reservation import database
from celery import Celery
from flask import jsonify
'''
logging.basicConfig(level=logging.INFO)
database.init_db()
app = connexion.App(__name__, specification_dir='static/')
app.add_api('swagger.yml')

# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
application = app.app
'''


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

# todo ora è commentato perchè
'''
def make_celery(app):
    celery = Celery(
        app.import_name,
        # broker=os.environ['CELERY_BROKER_URL'],
        # backend=os.environ['CELERY_BACKEND_URL']
        backend='redis://localhost:6379',
        broker='redis://localhost:6379'
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery(application)

"riprovo 30 volte, ritardo 10 secondi"
@celery.task(bind=True, max_retries=30)
def delete_reservations_task(self,reservations):
    try:
        return
    except Exception as e:
        self.retry(countdown=10)

'''



@application.teardown_appcontext
def shutdown_session(exception=None):
    database.db_session.remove()


if __name__ == '__main__':
    app.run(port=5100)
