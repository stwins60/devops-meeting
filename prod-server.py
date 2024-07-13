from app import app
from waitress import serve
import logging
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
import sentry_sdk

log_handler = logging.getLogger('waitress').handlers
root = logging.getLogger()
root.setLevel(logging.INFO)
root.handlers = log_handler

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

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=4, url_scheme='https')