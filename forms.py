from wtforms import Form, StringField, PasswordField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, Length

class RegistrationForm(Form):
    username = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    region = SelectField('Region', choices=[
        'Ashanti','Greater Accra','Central','Eastern','Western','Volta','Northern',
        'Upper East','Upper West','Bono','Bono East','Ahafo','Oti','Western North'
    ], validators=[DataRequired()])
    gender = SelectField('Gender', choices=['Male','Female'], validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()])
    role = SelectField('Role', choices=['Job Finder','Job Giver'], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

class JobForm(Form):
    title = StringField('Job Title', validators=[DataRequired()])
    description = TextAreaField('Job Description', validators=[DataRequired()])
    category = SelectField('Category', choices=['Web Development','Mobile App','Design','Writing','Other'], validators=[DataRequired()])
    budget = StringField('Budget')
