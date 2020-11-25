import os
from sqlalchemy import create_engine, Column, String, Integer, Unicode, PickleType, Boolean, Date
from sqlalchemy.schema import CheckConstraint
from sqlalchemy.orm import scoped_session, sessionmaker, validates
from sqlalchemy.ext.declarative import declarative_base


#DATABASEURI = os.environ['DATABASE_URI']
db = declarative_base()
#engine = create_engine(DATABASEURI, convert_unicode=True)
engine = create_engine('sqlite:///APIgateway.db', convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


def init_db():
    try:
        db.metadata.create_all(bind=engine)
    except Exception as e:
        print(e)


class User(db):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)

    email = Column(String, nullable=False, unique=True)  

    phone = Column(Unicode(128), CheckConstraint('length(phone) > 0'), nullable=False)

    firstname = Column(Unicode(128))
    lastname = Column(Unicode(128))
    dateofbirth = Column(Date)

    role = Column(String, nullable=False) 
    notification = Column(PickleType) 

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_anonymous = False


    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    @property
    def is_authenticated(self):
        return self._authenticated
        
    def get_id(self):
        return self.id