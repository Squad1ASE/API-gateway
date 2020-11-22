import os
from sqlalchemy import create_engine, Column, Integer, Float, Text, Unicode, DateTime, Boolean, ForeignKey, String
from sqlalchemy.orm import scoped_session, sessionmaker, validates, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
import datetime

db = declarative_base()

#DATABASEURI = os.environ['DATABASE_URI']
DATABASEURI = 'sqlite:///reservation.db'
db = declarative_base()
engine = create_engine(DATABASEURI, convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False,
                                             bind=engine))

def init_db():
    try:
        db.metadata.create_all(bind=engine)
        '''
        q = db_session.query(Reservation).filter(Reservation.id == 1).first()
        if q is None:
            example = Reservation()
            example.booker_id = 1
            example.restaurant_id = 1
            example.table_id = 1
            example.date = datetime.datetime.strptime("10/10/2020 12:00", "%d/%m/%Y %H:%M")
            #datetime.datetime.strptime(reservation_datetime_str, "%d/%m/%Y %H:%M")
            example.cancelled = False
            example.places = 2
            db_session.add(example)
            db_session.commit()
        q = db_session.query(Seat).filter(Seat.id == 1).first()
        if q is None:
            example = Seat()
            example.reservation_id = 1
            example.guests_email = 'test@test.com'
            example.confirmed = False
            r = db_session.query(Reservation).filter(Reservation.id == 1).first()
            r.seats.append(example)
            db_session.add(example)
            db_session.commit()
        '''

    except Exception as e:
        print(e)
    
class Reservation(db):
    __tablename__ = 'reservation'

    id = Column(Integer, primary_key=True, autoincrement=True)
    booker_id = Column(Integer)
    restaurant_id = Column(Integer)
    table_id = Column(Integer)
    date = Column(DateTime)
    cancelled = Column(Boolean, default=False)
    places = Column(Integer)
    seats = relationship("Seat", cascade="all,delete,delete-orphan", backref="reservation")

    def serialize(self):
        temp_dict = dict()
        for k, v in self.__dict__.items():
            if k[0] != '_':
                if isinstance(v, datetime.datetime):
                    #temp_dict.append_entry(k, v.__str__())
                    temp_dict[k] = v.__str__()
                else:
                    #temp_dict.append_entry(k, v)
                    temp_dict[k] = v
        seats = []
        for seat in self.seats:
            seats.append(seat.serialize())
        temp_dict['seats'] = seats

        return temp_dict
        #return dict([(k, v) for k, v in self.__dict__.items() if k[0] != '_'])


class Seat(db):
    __tablename__ = 'seat'

    id = Column(Integer, primary_key=True, autoincrement=True)
    reservation_id = Column(Integer, ForeignKey('reservation.id'))
    #reservation = relationship('Reservation', foreign_keys='Seat.reservation_id', backref=backref('seats', cascade="all, delete-orphan"))
    guests_email = Column(String)  
    confirmed = Column(Boolean, default=False)

    def serialize(self):
        return dict([(k, v) for k, v in self.__dict__.items() if k[0] != '_'])