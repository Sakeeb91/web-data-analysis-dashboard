import os


def init_monitoring():
    """Optional monitoring bootstrap. Initializes Sentry if SENTRY_DSN is set.
    Does nothing if sentry-sdk is not installed or DSN missing.
    """
    dsn = os.environ.get("SENTRY_DSN")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(),
                CeleryIntegration(),
                LoggingIntegration(level=None, event_level=None),
            ],
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        )
    except Exception:
        # Monitoring is optional in scaffold
        pass

