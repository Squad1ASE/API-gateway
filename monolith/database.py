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
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    email = db.Column(db.String, nullable=False, unique=True)  
    @validates('email')
    def validate_email(self, key, user):
        if('@' and '.' in user): #min email possible: a@b.c
            return user
        raise SyntaxError('Wrong email syntax')

    phone = db.Column(db.Unicode(128), db.CheckConstraint('length(phone) > 0'), nullable=False)

    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    password = db.Column(db.Unicode(128), nullable=False) 
    dateofbirth = db.Column(db.Date)

    role = db.Column(db.String, nullable=False) 
    @validates('role')
    def validate_role(self, key, user):
        if(user == 'admin' or user == 'customer' or user == 'owner' or user == 'ha'):
            return user
        raise SyntaxError('Wrong role assignment')

    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_anonymous = False


    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    def set_password(self, password):
        self.password = generate_password_hash(password)

    @property
    def is_authenticated(self):
        return self._authenticated

    def authenticate(self, password):
        checked = check_password_hash(self.password, password)
        self._authenticated = checked  # it is true if the user password is correct
        return self._authenticated

    def get_id(self):
        return self.id


class Restaurant(db.Model):
    __tablename__ = 'restaurant'

    class CUISINE_TYPES(FormEnum):
        italiana = 1
        cinese = 2
        messicana = 3
        giapponese = 4
        fast_food = 5
        pizzeria = 6

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = relationship('User', foreign_keys='Restaurant.owner_id')

    name = db.Column(db.Unicode(128), db.CheckConstraint('length(name) > 0'), nullable=False)
    lat = db.Column(db.Float, nullable=False)  # restaurant latitude
    lon = db.Column(db.Float, nullable=False)  # restaurant longitude
    phone = db.Column(db.Unicode(128), db.CheckConstraint('length(phone) > 0'), nullable=False) #TODO checklen?

    capacity = db.Column(db.Integer, db.CheckConstraint('capacity>0'), nullable=False)
    prec_measures = db.Column(db.Unicode(128), nullable=False)

    cuisine_type = db.Column(db.PickleType, db.CheckConstraint('length(cuisine_type) > 0'), nullable=False)

    # average time to eat, expressed in minutes 
    avg_time_of_stay = db.Column(db.Integer, db.CheckConstraint('avg_time_of_stay>=15'), nullable=False)

    tot_reviews = db.Column(db.Integer, db.CheckConstraint('tot_reviews>=0'), default=0)   # periodically updated in background
    avg_rating = db.Column(db.Float, db.CheckConstraint('avg_rating>=0 and avg_rating<=5'), default=0)
    likes = db.Column(db.Integer, db.CheckConstraint('likes>=0'), default=0)    # periodically updated in background

    @validates('owner_id')
    def validate_owner_id(self, key, owner_id):
        if (owner_id is None): raise ValueError("owner_id is None")
        if (owner_id <= 0): raise ValueError("owner_id must be > 0")
        return owner_id
        
    @validates('cuisine_type')
    def validate_cuisine_type(self, key, cuisine_types):
        if not isinstance(cuisine_types, list): raise ValueError("cuisine_type is not a list")
        if any(not isinstance(i,Restaurant.CUISINE_TYPES) for i in cuisine_types): raise ValueError("cuisine_type elements are not CUISINE_TYPES")
        if (len(cuisine_types) == 0): raise ValueError("cuisine_type is empty")
        return cuisine_types


class Table(db.Model):
    __tablename__ = 'table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship('Restaurant', foreign_keys='Table.restaurant_id',  backref=db.backref('tables', cascade="all, delete-orphan")) 

    table_name = db.Column(db.Unicode(128), db.CheckConstraint('length(table_name) > 0'), nullable=False)   
    capacity = db.Column(db.Integer, db.CheckConstraint('capacity>0'), nullable=False)

    @validates('restaurant_id')
    def validate_restaurant_id(self, key, restaurant_id):
        if (restaurant_id is None): raise ValueError("restaurant_id is None")
        if (restaurant_id <= 0): raise ValueError("restaurant_id must be > 0")
        return restaurant_id

    @validates('table_name')
    def validate_table_name(self, key, table_name):
        if (table_name is None): raise ValueError("table_name is None")
        if (len(table_name) == 0): raise ValueError("table_name is empty")
        return table_name

    @validates('capacity')
    def validate_capacity(self, key, capacity):
        if (capacity is None): raise ValueError("capacity is None")
        if (capacity <= 0): raise ValueError("capacity must be > 0")
        return capacity


class WorkingDay(db.Model):
    __tablename__ = 'working_day'

    class WEEK_DAYS(FormEnum):
        monday = 1
        tuesday = 2
        wednesday = 3
        thursday = 4
        friday = 5
        saturday = 6
        sunday = 7

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False, primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='WorkingDay.restaurant_id', backref=db.backref('workdays', cascade="all, delete-orphan"))  

    day = db.Column(db.PickleType, nullable=False, primary_key=True)
    work_shifts = db.Column(db.PickleType, nullable=False)  

    @validates('restaurant_id')
    def validate_restaurant_id(self, key, restaurant_id):
        if (restaurant_id is None): raise ValueError("restaurant_id is None")
        if (restaurant_id <= 0): raise ValueError("restaurant_id must be > 0")
        return restaurant_id
        
    @validates('day')
    def validate_day(self, key, day):
        if (day is None): raise ValueError("day is None")
        if not isinstance(day, WorkingDay.WEEK_DAYS): raise ValueError("day is not a WEEK_DAYS")
        return day

    @validates('work_shifts')
    def validate_work_shifts(self, key, work_shifts):
        if (work_shifts is None): raise ValueError("work_shifts is None")
        if not isinstance(work_shifts, list): raise ValueError("work_shifts is not a list")
        if (len(work_shifts) == 0): raise ValueError("work_shifts is empty")
        if (len(work_shifts) > 2): raise ValueError("work_shifts can contains at most two shifts")
        last = None
        for shift in work_shifts:
            if not isinstance(shift, tuple): raise ValueError("work_shifts element is not a list")
            if (len(shift) != 2): raise ValueError("work_shifts element is not a pair")
            for hour_to_check in shift:
                try:
                    hour = time.strptime(hour_to_check, '%H:%M')
                    if last is None:
                        last = hour
                    else:
                        if last >= hour:
                            raise ValueError("work_shifts contains non-incremental times")
                        last = hour
                except:
                    raise ValueError("incorrect format for hour")
        return work_shifts


class Like(db.Model):
    __tablename__ = 'like'

    liker_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    liker = relationship('User', foreign_keys='Like.liker_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='Like.restaurant_id')

    marked = db.Column(db.Boolean, default=False)  # True iff it has been counted in Restaurant.likes


class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    booker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    booker = relationship('User', foreign_keys='Reservation.booker_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='Reservation.restaurant_id')

    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))
    table = relationship('Table', foreign_keys='Reservation.table_id')

    date = db.Column(db.DateTime)
    cancelled = db.Column(db.Boolean, default=False)


class Seat(db.Model):
    __tablename__ = 'seat'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'))
    reservation = relationship('Reservation', foreign_keys='Seat.reservation_id', backref=db.backref('seats', cascade="all, delete-orphan"))

    guests_email = db.Column(db.String)  

    confirmed = db.Column(db.Boolean, default=False)


class Review(db.Model):
    __tablename__ = 'review'

    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    reviewer = relationship('User', foreign_keys='Review.reviewer_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='Review.restaurant_id')

    marked = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Unicode(128))
    date = db.Column(db.Date)


class Dish(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    restaurant = relationship('Restaurant', foreign_keys='Dish.restaurant_id', backref=db.backref('dishes', cascade="all, delete-orphan"))

    dish_name = db.Column(db.Unicode(128), db.CheckConstraint('length(dish_name) > 0'), nullable=False)
    price = db.Column(db.Float, db.CheckConstraint('price>0'), nullable=False)
    ingredients = db.Column(db.Unicode(128), db.CheckConstraint('length(ingredients) > 0'), nullable=False)

    @validates('restaurant_id')
    def validate_restaurant_id(self, key, restaurant_id):
        if (restaurant_id is None): raise ValueError("restaurant_id is None")
        if (restaurant_id <= 0): raise ValueError("restaurant_id must be > 0")
        return restaurant_id

    @validates('dish_name')
    def validate_dish_name(self, key, dish_name):
        if (dish_name is None): raise ValueError("dish_name is None")
        if (len(dish_name) == 0): raise ValueError("dish_name is empty")
        return dish_name

    @validates('price')
    def validate_price(self, key, price):
        if (price is None): raise ValueError("price is None")
        if (price <= 0): raise ValueError("price must be > 0")
        return price

    @validates('ingredients')
    def validate_ingredients(self, key, ingredients):
        if (ingredients is None): raise ValueError("ingredients is None")
        if (len(ingredients) == 0): raise ValueError("ingredients is empty")
        return ingredients


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
    