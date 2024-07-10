import requests
import pytz
from datetime import datetime

def get_user_timezone():
    try:
        # Use a public API to get the user's IP address
        response = requests.get('https://api64.ipify.org?format=json')
        data = response.json()

        # Get the user's IP address
        user_ip = data.get('ip')

        # Use a different API to get the user's time zone based on their IP
        timezone_response = requests.get(f'http://worldtimeapi.org/api/ip/{user_ip}')
        timezone_data = timezone_response.json()

        # Extract the time zone from the API response
        user_timezone = timezone_data.get('timezone')

        return user_timezone

    except Exception as e:
        print(f"Error fetching user timezone: {e}")
        return None

def change_time_based_on_timezone(user_timezone):
    try:
        # Get the current time in UTC
        utc_now = datetime.utcnow()

        # Set the time zone using pytz
        user_timezone_obj = pytz.timezone(user_timezone)
        user_local_time = utc_now.replace(tzinfo=pytz.utc).astimezone(user_timezone_obj)

        return user_local_time

    except Exception as e:
        print(f"Error changing time based on timezone: {e}")