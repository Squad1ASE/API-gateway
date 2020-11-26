import pytest
from database import db
from app import create_app
import tempfile
import os


@pytest.fixture
def test_app():
    app = create_app()

    app.config['WTF_CSRF_ENABLED'] = False  #this has been disabled to allows testing of forms
    temp_db, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.config['DATABASE']
    
    db.create_all(app=app)
    db.init_app(app=app)

    yield app, app.test_client()

    os.close(temp_db)