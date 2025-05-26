import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail configuration (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'sameerishassan@gmail.com'
    MAIL_PASSWORD = 'syma ypig plrw crfz'  # Use App Password, not your Gmail password

    # Host and URL configuration
    # Replace with your actual local IP (e.g., 192.168.0.101)
    SERVER_NAME = '172.17.241.41:5000'
    PREFERRED_URL_SCHEME = 'http'
