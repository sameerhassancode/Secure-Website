from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from config import Config
from models import db, User, LabReport
from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ResendVerificationForm, LabReportForm
from io import BytesIO
from xhtml2pdf import pisa
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        cnic = form.cnic.data
        if len(cnic) != 13 or not cnic.isdigit():
            flash('Invalid CNIC. CNIC should be exactly 13 digits long.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(cnic=cnic).first()
        if existing_user:
            flash(' This CNIC is already registered. Please use a different CNIC.', 'danger')
            return redirect(url_for('register'))

        user_data = {
            'username': form.username.data,
            'email': form.email.data,
            'phone': form.phone.data,
            'cnic': cnic,
            'password': generate_password_hash(form.password.data)
        }
        session['user_data'] = user_data

        token = s.dumps(form.email.data, salt='email-confirm')
        link = url_for('verify_email', token=token, _external=True)

        msg = Message('Verify your email', sender=app.config['MAIL_USERNAME'], recipients=[form.email.data])
        msg.body = f"Hi {form.username.data},\n\nPlease verify your email:\n{link}\n\nThanks!"
        mail.send(msg)

        return redirect(url_for('email_sent'))
    return render_template('register.html', form=form)

@app.route('/email-sent')
def email_sent():
    email = session.get('user_data', {}).get('email', '')
    return render_template('verify_notice.html', email=email)

@app.route('/verify/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
        user_data = session.get('user_data')
        if not user_data or user_data.get('email') != email:
            flash('Invalid email verification request.', 'danger')
            return redirect(url_for('index'))

        user = User(
            username=user_data['username'],
            email=user_data['email'],
            phone=user_data['phone'],
            cnic=user_data['cnic'],
            password=user_data['password'],
            is_verified=True
        )
        db.session.add(user)
        db.session.commit()
        session.pop('user_data', None)
        flash(' Email verified! You can now log in.', 'success')
        return redirect(url_for('login'))
    except SignatureExpired:
        flash('⏳ Verification link expired. Please register again.', 'danger')
        return redirect(url_for('register'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if not user.is_verified:
                flash('⚠️ Please verify your email first.', 'warning')
                session['pending_email'] = user.email
                return redirect(url_for('email_sent'))
            login_user(user)
            return redirect(url_for('admin_dashboard' if user.is_admin else 'user_dashboard'))
        flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard/user')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    reports = LabReport.query.filter_by(cnic=current_user.cnic).all()
    return render_template('dashboard_user.html', reports=reports)

@app.route('/dashboard/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    users = User.query.all()
    return render_template('dashboard_admin.html', users=users)

@app.route('/get_user_info/<cnic>', methods=['GET'])
def get_user_info(cnic):
    user = User.query.filter_by(cnic=cnic).first()
    if user:
        return jsonify({
            'username': user.username,
            'phone': user.phone
        })
    return jsonify({'error': 'User not found'}), 404

@app.route('/upload_report', methods=['GET', 'POST'])
@login_required
def upload_report():
    if not current_user.is_admin:
        flash("Only admin can access this page.", "danger")
        return redirect(url_for('index'))

    form = LabReportForm()
    if form.validate_on_submit():
        report = LabReport(
            cnic=form.cnic.data,
            patient_name=form.patient_name.data,
            patient_phone=form.patient_phone.data,
            report_type=form.report_type.data,
            report_data=form.report_data.data
        )
        db.session.add(report)
        db.session.commit()
        flash(" Report uploaded successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template("report.html", form=form)

@app.route('/report/<int:report_id>/download')
@login_required
def download_report_pdf(report_id):
    report = LabReport.query.get_or_404(report_id)
    if report.cnic != current_user.cnic:
        flash(" Access denied.", "danger")
        return redirect(url_for('user_dashboard'))

    html = render_template('report_pdf.html', report=report)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return 'PDF generation failed', 500

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{report.id}.pdf'
    return response

@app.route('/report/<int:report_id>/view')
@login_required
def view_report_pdf(report_id):
    report = LabReport.query.get_or_404(report_id)
    if report.cnic != current_user.cnic:
        flash(" Access denied.", "danger")
        return redirect(url_for('user_dashboard'))

    html = render_template('report_pdf.html', report=report)
    result = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)
    if pisa_status.err:
        return 'PDF generation failed', 500

    response = make_response(result.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=report_{report.id}.pdf'
    return response

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='reset-password')
            link = url_for('reset_password', token=token, _external=True)

            msg = Message('Reset Your Password', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f"Hi {user.username},\n\nClick the link to reset your password:\n{link}\n\nThis link will expire in 1 hour."
            mail.send(msg)
            flash('✅ Password reset link sent to your email.', 'info')
            return redirect(url_for('login'))
        flash(' Email not found.', 'danger')
    return render_template('forgot_password.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)
    except SignatureExpired:
        flash(' Reset link expired. Try again.', 'danger')
        return redirect(url_for('forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(form.password.data)
            db.session.commit()
            flash(' Password has been reset.', 'success')
            return redirect(url_for('login'))
        flash(' User not found.', 'danger')
        return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', form=form)

@app.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    form = ResendVerificationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.is_verified:
                flash(' Email is already verified.', 'success')
                return redirect(url_for('login'))
            token = s.dumps(user.email, salt='email-confirm')
            link = url_for('verify_email', token=token, _external=True)

            msg = Message('Verify Your Email', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f"Hi {user.username},\n\nPlease verify your email:\n{link}\n\nThanks!"
            mail.send(msg)

            flash('📧 Verification email resent.', 'info')
            return redirect(url_for('email_sent'))
        flash(' Email not found.', 'danger')
    return render_template('resend_verification.html', form=form)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin_email = 'admin@gmail.com'
        admin = User.query.filter_by(email=admin_email).first()
        if not admin:
            admin_user = User(
                username='Admin',
                email=admin_email,
                phone='0000000000',
                cnic='0000000000000',
                password=generate_password_hash('admin@123'),
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(" Default admin created: admin@gmail.com / admin@123")

    app.run(host='0.0.0.0', port=5000, debug=True)
