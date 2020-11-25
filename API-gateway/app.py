import connexion, logging
from flask import jsonify
from database import db_session, init_db
import requests

        
RESTAURANT_SERVICE = "http://0.0.0.0:5060/"


def create_app():
    logging.basicConfig(level=logging.INFO)
    app = connexion.App(__name__, specification_dir='static/')
    app.add_api('swagger.yml')

    

    init_db()
    return app


# set the WSGI application callable to allow using uWSGI:
# uwsgi --http :8080 -w app
app = create_app()
application = app.app
# TODO THIS SECTION MUST BE REMOVED, ONLY FOR DEMO
# already tested EndPoints are used to create examples
application.config['WTF_CSRF_ENABLED'] = False

@application.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


if __name__ == '__main__':
    app.run(port=5000)