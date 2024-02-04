from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
import secrets
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, date

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'email' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('auth_sign_in'))
    return wrap

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(64)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class MeetingForm(FlaskForm):
    time_zone = SelectField('Time Zone', choices=[('CST', 'CST'), ('EST', 'EST'), ('PST', 'PST')])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_name = db.Column(db.String(100), nullable=False)
    tag = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    time_zone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    


@app.route('/')
def index():
    # get all meetings
    meetings = Meeting.query.all()
    return render_template('member-landing.html', meetings=meetings)


@app.route('/admin')
@is_logged_in
def admin():
    meetings = Meeting.query.all()
    return render_template('admin.html', meetings=meetings)

@app.route('/auth_sign_in', methods=['GET', 'POST'])
def auth_sign_in():
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user:
                if sha256_crypt.verify(password, user.password):
                    session['email'] = email
                    flash('You are now logged in', 'success')
                    return redirect(url_for('admin'))
                else:
                    flash('Invalid password', 'danger')
                    return redirect(url_for('auth_sign_in'))

            return redirect(url_for('index'))
    except Exception as e:
        return str(e)
    return render_template('auth-sign-in.html')

@app.route('/auth_sign_out')
def auth_sign_out():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route('/auth_sign_up', methods=['GET', 'POST'])
def auth_sign_up():
    if request.method == 'POST':
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        email = request.form['email']
        password = sha256_crypt.encrypt(str(request.form['password']))
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can log in', 'success')
        return redirect(url_for('auth_sign_in'))
    return render_template('auth-sign-up.html')

@app.route('/page_add_event')
def page_add_event():
    return render_template('page-add-event.html')

@app.route('/new_event')
def new_event():
    form = MeetingForm()

    return render_template('page-new-event.html', form=form)


@app.route('/add_event', methods=['POST', 'GET'])
def add_event():
    form = MeetingForm()

    event_name = request.form['event_name']
    tag = request.form['tag']
    description = request.form['description']
    link = request.form['link']
    date = request.form['date']
    time = request.form['time']
    time_zone = form.time_zone.data

    print(event_name, description, link, date, time, time_zone)

    date_obj = datetime.strptime(date, '%Y-%m-%d').date()

    with app.app_context():
        new_meeting = Meeting(event_name=event_name, tag=tag, description=description, link=link, time=time, time_zone=time_zone, date=date_obj)
        db.session.add(new_meeting)
        db.session.commit()

    return redirect(url_for('index'))

@app.template_filter('format_time')
def format_time(value):
    dt = datetime.strptime(value, '%H:%M')
    return dt.strftime('%I:%M %p %Z')

@app.template_filter('format_date')
def format_date(value):
    dt = datetime.strptime(value, '%Y-%m-%d')
    return dt.strftime('%A, %B %d, %Y')
# def add_event_get():
#     form = MeetingForm()
#     meetings = Meeting.query.all()
#     if 'username' not in session or session['username'] != 'admin':
#         return redirect(url_for('index'))
#     return render_template('add_meeting.html', form=form, meetings=meetings)

@app.route('/main_my_schedule')
def main_my_schedule():
    return render_template('main-my-schedule.html')

@app.route('/main_integration')
def main_integration():
    return render_template('main-integration.html')

@app.route('/page_workflow')
def page_workflow():
    return render_template('page-workflow.html')



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)