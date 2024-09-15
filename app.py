from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField
import secrets
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime, date
import pytz
import helper
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sentry_sdk
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            logging.error('Unauthorized, Please login')
            return redirect(url_for('auth_sign_in'))
    return wrap

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(64)

headers = {
    'Content-Type': 'text/html',
    'charset': 'utf-8',
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Access-Control-Allow-Headers, Authorization, X-Requested-With",
    "Authorization": "Bearer " + secrets.token_urlsafe(64),
}

sentry_sdk.init(
    dsn="https://996b61df962344767cb64a45f8dc9e60@sentry.africantech.dev/7",
    enable_tracing=True,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    integrations = [
        AsyncioIntegration(),
        FlaskIntegration(
            transaction_style="url"
        ),
        AioHttpIntegration(
            transaction_style="method_and_path_pattern"
        )
    ]
)

MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD').replace('@', '%40')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_DB = os.getenv('MYSQL_DB')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')



# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meetings.db'
# app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:123456@localhost/meetings"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DB}"
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
    description = db.Column(db.String(800), nullable=False)
    link = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    time_zone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
  
def convert_to_standard_time(iso_time):
    # Parse the time in the format YYYYMMDDTHHMMSSZ (UTC format)
    dt = datetime.strptime(iso_time, "%Y%m%dT%H%M%SZ")
    # Convert to the desired format
    return dt.strftime("%Y%m%dT%H%M%S")

def generate_google_calendar_url(event_name, event_date, event_time, event_description):
    # Combine the event date and time to create a datetime object
    start_time = datetime.combine(event_date, event_time)

    # Calculate the end time (2 hours after the start time)
    end_time = start_time + timedelta(hours=2)
    
    # Format the start and end time for Google Calendar (YYYYMMDDTHHmmSSZ)
    start = start_time.strftime("%Y%m%dT%H%M%SZ")
    end = end_time.strftime("%Y%m%dT%H%M%SZ")
    
    start_standard_time = convert_to_standard_time(start)
    end_standard_time = convert_to_standard_time(end)
    
    # Construct the Google Calendar URL
    google_calendar_url = (
        f"https://www.google.com/calendar/render?action=TEMPLATE&text={event_name}&"
        f"dates={start_standard_time}/{end_standard_time}&details={event_description}&sf=true&output=xml"
    )
    
    return google_calendar_url

def generate_ics_file(event_name, event_date, event_time, event_description):
    # Convert event_date string to datetime object
    event_date = datetime.strptime(event_date, '%A, %B %d, %Y')
    
    # Convert event_time string (e.g., '07:30 PM') to datetime object
    event_time = datetime.strptime(event_time, '%I:%M %p').time()

    # Combine the date and time into a single datetime object
    start_time = datetime.combine(event_date, event_time)

    # Calculate the end time (assuming a 2-hour duration for the event)
    end_time = start_time + timedelta(hours=2)

    # Format the start and end times for the ICS file
    start = start_time.strftime("%Y%m%dT%H%M%S")
    end = end_time.strftime("%Y%m%dT%H%M%S")

    # Create ICS file content without time zone information
    ics_content = (
        "BEGIN:VCALENDAR\n"
        "VERSION:2.0\n"
        "PRODID:-//DevOps FullStack Demo Meeting//EN\n"
        "BEGIN:VEVENT\n"
        f"DTSTART:{start}\n"
        f"DTEND:{end}\n"
        f"SUMMARY:{event_name}\n"
        f"DESCRIPTION:{event_description}\n"
        "END:VEVENT\n"
        "END:VCALENDAR"
    )
    
    return ics_content

@app.route('/download_ics')
def download_ics():
    event_name = request.args.get('event_name')
    event_date = request.args.get('event_date')
    event_time = request.args.get('event_time')
    event_description = request.args.get('event_description')

    # Generate ICS content
    ics_content = generate_ics_file(event_name, event_date, event_time, event_description)
    
    # Create and send response with ICS file
    response = make_response(ics_content, 200)
    response.headers["Content-Type"] = "text/calendar"
    response.headers["Content-Disposition"] = f"attachment; filename={event_name}.ics"
    
    return response

@app.route('/')
def index():
    # Get all meetings
    meetings = Meeting.query.all()
    user_timezone = helper.get_user_timezone()  # Assuming this returns a valid timezone string like "America/New_York"
    user_timezone_obj = pytz.timezone(user_timezone)
    meetings_data = []

    for meeting in meetings:
        meeting_time = meeting.time  # Example: '19:30' (7:30 PM in 24-hour format)
        meeting_time_zone = meeting.time_zone  # Example: 'America/Chicago', 'CST', etc.

        # Map timezone abbreviations (like 'CST') to full timezone names if necessary
        TIMEZONE_MAPPING = {
            'CST': 'America/Chicago',
            'EST': 'America/New_York',
            'PST': 'America/Los_Angeles',
            'MST': 'America/Denver',
            # Add other timezone mappings as needed
        }

        # Check if meeting_time_zone is a timezone abbreviation and map it to a full timezone
        if meeting_time_zone in TIMEZONE_MAPPING:
            meeting_time_zone = TIMEZONE_MAPPING[meeting_time_zone]

        # Combine date and time to create a naive datetime object (no timezone info yet)
        meeting_time_obj = datetime.strptime(meeting_time, '%H:%M').time()
        meeting_datetime = datetime.combine(meeting.date, meeting_time_obj)

        # Localize the datetime to the stored timezone (meeting's timezone)
        if meeting_time_zone:
            try:
                meeting_timezone_obj = pytz.timezone(meeting_time_zone)
                # Localize the naive datetime object to the meeting's timezone
                meeting_datetime = meeting_timezone_obj.localize(meeting_datetime)
            except pytz.UnknownTimeZoneError:
                logging.error(f"Unknown timezone: {meeting_time_zone}")
                # Fallback to UTC if timezone is unknown
                meeting_datetime = pytz.utc.localize(meeting_datetime)
        else:
            # If no timezone is specified, assume it's UTC
            meeting_datetime = pytz.utc.localize(meeting_datetime)

        # Convert the meeting datetime to the user's timezone
        meeting_datetime_user_tz = meeting_datetime.astimezone(user_timezone_obj)

        # Format the datetime to 12-hour format with AM/PM for display
        formatted_time = meeting_datetime_user_tz.strftime('%I:%M %p')  # '07:30 PM'

        # Generate Google Calendar URL (for event in UTC format)
        google_calendar_url = generate_google_calendar_url(
            meeting.event_name,
            meeting_datetime_user_tz.date(),  # Pass only the date part
            meeting_datetime_user_tz.time(),  # Pass only the time part
            meeting.description
        )

        # Add data to meetings_data
        meetings_data.append({
            'event_name': meeting.event_name,
            'tag': meeting.tag,
            'description': meeting.description,
            'link': meeting.link,
            'time': formatted_time,  # Display time in 12-hour format (e.g., 7:30 PM)
            'date': meeting_datetime_user_tz.strftime('%A, %B %d, %Y'),
            'time_zone': user_timezone,
            'google_calendar_url': google_calendar_url  # Add Google Calendar link
        })

    logging.info('Meetings data: %s', meetings_data)

    response = make_response(
        render_template('member-landing.html', meetings=meetings, meetings_data=meetings_data, user_timezone=user_timezone),
        200
    )
    response.headers.update(headers)
    return response




@app.route('/admin')
@is_logged_in
def admin():
    meetings = Meeting.query.all()
    logging.info('Meetings: %s', meetings)
    response = make_response(
        render_template('admin.html', meetings=meetings),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/auth_sign_in', methods=['GET', 'POST'])
def auth_sign_in():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            # user = User.query.filter_by(email=email).first():
                # if sha256_crypt.verify(password, user.password):
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                logging.info('Logged in as admin')
                session['username'] = username
                flash('You are now logged in', 'success')
                return redirect(url_for('admin'))
            else:
                logging.error('Invalid password')
                flash('Invalid password', 'danger')
                return redirect(url_for('auth_sign_in'))

        response = make_response(
        render_template('auth-sign-in.html'),
        200
    )
        response.headers.update(headers)
        return response
    except Exception as e:
        return str(e)
    

@app.route('/auth_sign_out')
def auth_sign_out():
    session.clear()
    logging.info('Logged out')
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route('/auth_sign_up', methods=['GET', 'POST'])
def auth_sign_up():
    if request.method == 'POST':
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        email = request.form['email']
        password = sha256_crypt.hash(str(request.form['password']))
        user = User(first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can log in', 'success')
        logging.info('User registered')
        return redirect(url_for('auth_sign_in'))
    response = make_response(
        render_template('auth-sign-up.html'),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/page_add_event')
def page_add_event():
    logging.info('Add event page')
    response = make_response(
        render_template('page-add-event.html'),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/new_event')
def new_event():
    form = MeetingForm()
    logging.info('New event page')
    response = make_response(
        render_template('page-new-event.html', form=form),
        200
    )
    response.headers.update(headers)
    return response


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

    # print(event_name, description, link, date, time, time_zone)

    date_obj = datetime.strptime(date, '%Y-%m-%d').date()

    with app.app_context():
        new_meeting = Meeting(event_name=event_name, tag=tag, description=description, link=link, time=time, time_zone=time_zone, date=date_obj)
        db.session.add(new_meeting)
        db.session.commit()
        logging.info('New event added')

    return redirect(url_for('index'))

@app.route('/edit_event/<int:id>', methods=['POST', 'GET'])
@is_logged_in
def edit_event(id):
    form = MeetingForm()
    meeting = db.session.query(Meeting).filter(Meeting.id == id).first()
    if request.method == 'POST':
        meeting.event_name = request.form['event_name']
        meeting.tag = request.form['tag']
        meeting.description = request.form['description']
        meeting.link = request.form['link']
        meeting.date = request.form['date']
        meeting.time = request.form['time']
        meeting.time_zone = form.time_zone.data
        db.session.commit()
        logging.info('Event edited')
        return redirect(url_for('admin'))
    form.time_zone.data = meeting.time_zone
    logging.info('Edit event page')
    response = make_response(
        render_template('edit_event.html', meeting=meeting, form=form),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/delete_event/<int:id>', methods=['POST', 'GET'])
@is_logged_in
def delete_event(id):
    meeting = db.session.query(Meeting).filter(Meeting.id == id).first()
    db.session.delete(meeting)
    db.session.commit()
    logging.info('Event deleted')
    return redirect(url_for('admin'))

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
    response = make_response(
        render_template('main-my-schedule.html'),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/main_integration')
def main_integration():
    response = make_response(
        render_template('main-integration.html'),
        200
    )
    response.headers.update(headers)
    return response

@app.route('/page_workflow')
def page_workflow():
    response = make_response(
        render_template('page-workflow.html'),
        200
    )
    response.headers.update(headers)
    return response

@app.errorhandler(404)
def page_not_found(e):

    response = make_response(
        render_template('404.html'),
        404
    )
    logging.error('Page not found')
    response.headers.update(headers)
    return response

@app.errorhandler(500)
def internal_server_error(e):

    response = make_response(
        render_template('500.html'),
        500
    )
    logging.error('Internal server error')
    response.headers.update(headers)
    return response

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)