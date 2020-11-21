from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form, BooleanField
from wtforms.validators import DataRequired, Length, Email, NumberRange, ValidationError
from monolith.database import Restaurant, WorkingDay
import ast


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    password = f.PasswordField('password', validators=[DataRequired(), Length(8,20)])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    phone = f.StringField('phone', validators=[DataRequired()])
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired(), Length(8,20)])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    role = f.StringField('role', validators=[DataRequired()])
    display = ['email', 'phone', 'firstname', 'lastname', 'password', 'dateofbirth', 'role']


class EditUserForm(FlaskForm):
    phone = f.StringField('phone', validators=[DataRequired()])
    old_password = f.PasswordField('old_password', validators=[DataRequired(), Length(8,20)])
    new_password = f.PasswordField('new_password', validators=[Length(8,20)])
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
        choices = WorkingDay.WEEK_DAYS.choices(),
        coerce = WorkingDay.WEEK_DAYS.coerce, 
        validators=[DataRequired()]
    )
    work_shifts = f.StringField('Work shifts', validators=[DataRequired()])

    def validate_work_shifts(form, field):
        try:
            str_shifts = '[' + field.data + ']'
            shifts = list(ast.literal_eval(str_shifts))
            trial_working_day = WorkingDay()
            trial_working_day.work_shifts = shifts
        except:
            raise ValidationError("expected format: ('HH:MM','HH:MM'),('HH:MM','HH:MM')")


class RestaurantForm(FlaskForm):
    name = f.StringField('Name', validators=[DataRequired()])
    lat = f.FloatField('Latitude', validators=[DataRequired()])
    lon = f.FloatField('Longitude', validators=[DataRequired()])
    phone = f.StringField('Phone', validators=[DataRequired()])

    # Note: the capacity is automatically derived from tables settings

    cuisine_type = f.SelectMultipleField(
        'Cuisine types', 
        choices = Restaurant.CUISINE_TYPES.choices(),
        coerce = Restaurant.CUISINE_TYPES.coerce, 
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
        choices = Restaurant.CUISINE_TYPES.choices(),
        coerce = Restaurant.CUISINE_TYPES.coerce
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
