from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship, validates  # is Object map scheme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.orm import backref
from enum import Enum
import time

db = SQLAlchemy(session_options={

    'expire_on_commit': False

})


# class that the enums used in the underlying classes 
# should inherit to facilitate their management in forms
class FormEnum(Enum):
    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(int(item)) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)

    def __lt__(self, other):
        return self.value < other.value


# the following consist of tables inside the db tables are defined using model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String, nullable=False, unique=True)  

    phone = db.Column(db.Unicode(128), db.CheckConstraint('length(phone) > 0'), nullable=False)

    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    dateofbirth = db.Column(db.Date)

    role = db.Column(db.String, nullable=False) 
    notification = db.Column(db.PickleType) 

    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_anonymous = False


    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    @property
    def is_authenticated(self):
        return self._authenticated
        
    def get_id(self):
        return self.id


class Quarantine(db.Model):
    __tablename__ = 'quarantine'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', foreign_keys='Quarantine.user_id')

    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    in_observation = db.Column(db.Boolean, default=True) #True=can't book


class Notification(db.Model):
    __tablename__ = 'notification'

    # questa parte non serve, si può integrare dentro swagger direttamente
    # si può usare direttamente come lista 
    class TYPE(FormEnum):
        contact_with_positive = 1
        reservation_canceled = 2
        reservation_with_positive = 3

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', foreign_keys='Notification.user_id')

    email = db.Column(db.Unicode(128), db.CheckConstraint('length(email) > 0'), nullable=False)  
    message = db.Column(db.Unicode(128), db.CheckConstraint('length(message) > 0'), nullable=False)
    pending = db.Column(db.Boolean, default=True)
    type_ = db.Column(db.PickleType, nullable=False)  
    date = db.Column(db.DateTime, nullable=False)

    @validates('user_id')
    def validate_user_id(self, key, user_id):
        if user_id is not None:
            if (user_id <= 0): raise ValueError("user_id must be > 0")
        return user_id
        
    @validates('email')
    def validate_email(self, key, email):
        if email is None: raise ValueError("type_ is None")
        if (len(email) == 0): raise ValueError("email is empty")
        if('@' and '.' in email): #min email possible: a@b.c
            return email
        raise ValueError('Wrong email syntax')

    @validates('message')
    def validate_message(self, key, message):
        if (message is None): raise ValueError("message is None")
        if (len(message) == 0): raise ValueError("message is empty")
        return message
    
    @validates('pending')
    def validate_pending(self, key, pending):
        if (pending is None): raise ValueError("pending is None")
        return pending

    @validates('type_')
    def validate_type_(self, key, type_):
        if type_ is None: raise ValueError("type_ is None")
        if not isinstance(type_, Notification.TYPE): raise ValueError("type_ is not a Notification.TYPE")
        return type_

    @validates('date')
    def validate_date(self, key, date):
        if (date is None): raise ValueError("date is None")
        return date
    
