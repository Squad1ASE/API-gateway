from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange, ValidationError
import ast
from monolith.static.enum import CUISINE_TYPES, WEEK_DAYS
import time


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    phone = f.StringField('phone', validators=[DataRequired()])
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    role = f.StringField('role', validators=[DataRequired()])
    display = ['email', 'phone', 'firstname', 'lastname', 'password', 'dateofbirth', 'role']


class EditUserForm(FlaskForm):
    phone = f.StringField('phone', validators=[DataRequired()])
    old_password = f.PasswordField('old_password', validators=[DataRequired(), Length(1,8)])
    new_password = f.PasswordField('new_password', validators=[DataRequired(), Length(1,8)])
    display = ['phone', 'old_password', 'new_password']
    

class DishForm(Form):
    """Subform.

    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    dish_name = f.StringField('Name', validators=[DataRequired()])
    price = f.FloatField('Price', validators=[DataRequired()])
    ingredients = f.StringField('Ingredients', validators=[DataRequired()])


class TableForm(Form):
    """Subform.

    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    table_name = f.StringField('Name', validators=[DataRequired()])
    capacity = f.IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1)])


class WorkingDayForm(Form):
    """Subform.

    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    day = f.SelectField(
        'Day', 
        choices = [(weekday,weekday) for weekday in WEEK_DAYS],
        validators=[DataRequired()]
    )
    work_shifts = f.StringField('Work shifts', validators=[DataRequired()])

    def validate_work_shifts(form, field):
        str_shifts = '[' + field.data + ']'
        work_shifts = list(ast.literal_eval(str_shifts))
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
    '''
    def validate_work_shifts(form, field):
        try:
            str_shifts = '[' + field.data + ']'
            shifts = list(ast.literal_eval(str_shifts))
            for shift in shifts:
                if not isinstance(shift, tuple) or len(shift) != 2:
                    raise Exception()
                
        except:
            raise ValidationError("expected format: ('HH:MM','HH:MM'),('HH:MM','HH:MM')")
    '''

class RestaurantForm(FlaskForm):

    name = f.StringField('Name', validators=[DataRequired()])
    lat = f.FloatField('Latitude', validators=[DataRequired()])
    lon = f.FloatField('Longitude', validators=[DataRequired()])
    phone = f.StringField('Phone', validators=[DataRequired()])

    # Note: the capacity is automatically derived from tables settings

    cuisine_type = f.SelectMultipleField(
        'Cuisine types', 
        choices = [(cuisine,cuisine) for cuisine in CUISINE_TYPES],
        validators=[DataRequired()]
    )
    prec_measures = f.TextAreaField('Precautionary measures',validators=[DataRequired()])
    avg_time_of_stay = f.IntegerField('Average time of stay (in minutes)', validators=[DataRequired(), NumberRange(min=15)])

    workingdays = f.FieldList(f.FormField(WorkingDayForm), min_entries=1, max_entries=7)
    tables = f.FieldList(f.FormField(TableForm), min_entries=1, max_entries=100)
    dishes = f.FieldList(f.FormField(DishForm), min_entries=1, max_entries=100)

    display = ['name', 'lat', 'lon', 'phone', 'cuisine_type', 'prec_measures', 'avg_time_of_stay']
    
    def validate_workingdays(form, field):
        days_already_added = []
        for wd in field.data:
            if wd['day'] in days_already_added:
                raise ValidationError("There cannot be two working days with the same day")
            else:
                days_already_added.append(wd['day'])
                
                
class GetPatientInformationsForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])
    display = ['email']

class SubReservationPeopleEmail(Form):
    email = f.StringField('email', validators=[Length(10, 64), Email()])

class ReservationPeopleEmail(FlaskForm):
    guest = f.FieldList(f.FormField(SubReservationPeopleEmail), min_entries=1, max_entries=100)
    display = ['guest']

class ReservationRequest(FlaskForm):
    date = f.DateField('date', format='%d/%m/%Y', validators=[DataRequired()])
    time = f.DateField('time', format='%H:%M', validators=[DataRequired()])
    guests = f.IntegerField('guests', validators=[DataRequired(), NumberRange(min=1)])
    display = ['date','time','guests']

class RestaurantSearch(FlaskForm):
    name = f.StringField('Name')
    lat = f.StringField('Latitude')
    lon = f.StringField('Longitude')

    cuisine_type = f.SelectMultipleField(
        'Cuisine types', 
        choices = [(cuisine,cuisine) for cuisine in CUISINE_TYPES],
        validators=[DataRequired()]
    )

    display = ['name', 'lat', 'lon', 'cuisine_type']

class ReviewForm(FlaskForm):
    rating = f.IntegerField('Rating', validators=[NumberRange(min=0, max=5)])
    comment = f.TextAreaField('Comment', validators=[DataRequired()])
    display = ['rating', 'comment']

class EditRestaurantForm(FlaskForm):
    phone = f.StringField('Phone', validators=[DataRequired()])
    #tables = f.FieldList(f.FormField(TableForm), min_entries=1, max_entries=100)
    dishes = f.FieldList(f.FormField(DishForm), min_entries=1, max_entries=100)
    display = ['phone']
