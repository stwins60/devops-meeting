from app import app
from waitress import serve
import logging

log_handler = logging.getLogger('waitress').handlers
root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers = log_handler

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)