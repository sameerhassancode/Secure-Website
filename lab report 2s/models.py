#  Updated models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    cnic = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<User {self.username}>'

class LabReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cnic = db.Column(db.String(15), db.ForeignKey('user.cnic'), nullable=False)
    patient_name = db.Column(db.String(100), nullable=False)
    patient_phone = db.Column(db.String(15), nullable=False)
    report_type = db.Column(db.String(100), nullable=False)
    report_data = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref='reports', lazy=True)

    def __repr__(self):
        return f'<LabReport {self.id}>'
