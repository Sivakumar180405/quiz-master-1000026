from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from models.models import User, db, Subject, Chapter, Quiz, Question, Score

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')

        admin = User.query.filter_by(email=email, is_admin=True).first()

        if admin and admin.password == pw: 
            login_user(admin)
            return redirect(url_for('main.admin_dashboard'))

    return render_template('admin_login.html')

@main.route('/admin/dashboard')
def admin_dashboard():
    subjects = Subject.query.all()
    return render_template('admin_db.html', subjects=subjects)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('main.user_dashboard'))
    return render_template('login.html')

@main.route('/dashboard')
@login_required
def user_dashboard():
    subjects = Subject.query.all()
    return render_template('db.html', subjects=subjects)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))