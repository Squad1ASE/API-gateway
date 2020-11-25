from flask import Blueprint, render_template, redirect, request, make_response
from flask_login import (current_user, login_user, logout_user,
                         login_required)

from monolith.database import db, User
from monolith.forms import LoginForm
import requests
from datetime import datetime

auth = Blueprint('auth', __name__)

USER_SERVICE = 'http://127.0.0.1:5060/'


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user is not None and hasattr(current_user, 'id'):
        return redirect('/')

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email, password = form.data['email'], form.data['password']

            login_dict = dict(
                email=form.data['email'],
                password=form.data['password']
            )

            reply = requests.post(USER_SERVICE+'login', json=login_dict)
            reply_json = reply.json()

            if reply.status_code == 200:
                user = User()
                user.id = int(reply_json['id'])
                user.email = reply_json['email']
                user.phone = reply_json['phone']
                user.firstname = reply_json['firstname']
                user.lastname = reply_json['lastname']
                user.dateofbirth = datetime.strptime(reply_json['dateofbirth'], "%Y-%m-%d")
                user.role = reply_json['role']
                user.is_admin = bool(reply_json['is_admin'])
                user.is_anonymous = bool(reply_json['is_anonymous'])
                user.notification = reply_json['notification']
                
                db.session.add(user)
                db.session.commit()
                login_user(user)
                return redirect('/')
            else:
                form.password.errors.append(reply_json['detail'])
                return render_template('login.html', form=form)

        else:
            return make_response(render_template('login.html', form=form), 400)

    return render_template('login.html', form=form)


@auth.route("/logout")
@login_required
def logout():
    user = db.session.query(User).filter_by(id = current_user.id)
    user.delete()
    db.session.commit()
    logout_user()
    return redirect('/')
