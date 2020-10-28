import unittest
from monolith.database import db, User
from monolith.app import app
from monolith.forms import UserForm
import datetime

app_ctx = app.app_context()
app_ctx.push()
tested_app = app.test_client()

class TestUser(unittest.TestCase):

    def test_users(self):
        q = db.session.query(User)
        user = q.first()

    def test_login_form(self):
        '''
        reply = tested_app.post('/create_user',
                    data=dict(
                        email='myemail_test@test.com',
                        firstname='myfirstname_test',
                        lastname='mylastname_test',
                        password='passw',
                        dateofbirth='10/10/2000'
                    )
                )
        

        form = UserForm()
        form.email='myemail_test@test.com',
        form.firstname='myfirstname_test',
        form.lastname='mylastname_test',
        form.password='passw',
        form.dateofbirth='10/10/2000'
        #form.populate_obj(user)
        '''

        form_dict = {
            'email':'myemail_test@test.com',
            'firstname':'myfirstname_test',
            'lastname':'mylastname_test',
            'password':'passw',
            'dateofbirth':'10/10/2000'}

        #reply = tested_app.post('/create_user', data=form_dict)
        reply = tested_app.post('/create_user', data=form_dict)
        #print(reply.status_code)

        #self.assertEqual(status, 555)

    
