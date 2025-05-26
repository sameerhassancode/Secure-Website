from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Email, Length

# Register Form (Single Password Field)
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    cnic = StringField('CNIC', validators=[DataRequired(), Length(min=13, max=13)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

# Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# Forgot Password Form
class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

# Reset Password Form (single password only)
class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Reset Password')

# Resend Verification Form
class ResendVerificationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Resend Verification Email')

#  Enhanced Report Upload Form
class LabReportForm(FlaskForm):
    cnic = StringField('User CNIC', validators=[DataRequired(), Length(min=13, max=13)])
    patient_name = StringField('Patient Name', render_kw={'readonly': True})
    patient_phone = StringField('Phone Number', render_kw={'readonly': True})
    report_type = SelectField('Report Type', choices=[
        ('Blood Test', 'Blood Test'),
        ('X-Ray', 'X-Ray'),
        ('MRI', 'MRI'),
        ('Covid Report', 'Covid Report'),
        ('General Checkup', 'General Checkup')
    ], validators=[DataRequired()])
    report_data = TextAreaField('Report Content', validators=[DataRequired()])
    submit = SubmitField('Upload Report')
