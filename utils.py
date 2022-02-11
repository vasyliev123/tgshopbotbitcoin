import configloader
import os

if configloader.user_cfg["ErrorReporting"]["sentry_token"] != \
        "https://00000000000000000000000000000000:00000000000000000000000000000000@sentry.io/0000000":
    import raven
    import raven.exceptions
    try:
        release = raven.fetch_git_sha(os.path.dirname(__file__))
    except raven.exceptions.InvalidGitRepository:
        release = "Unknown"
    sentry_client = raven.Client(configloader.user_cfg["ErrorReporting"]["sentry_token"],
                                 release=release,
                                 environment="Dev" if __debug__ else "Prod")
else:
    sentry_client = None

def telegram_html_escape(string: str):
    return string.replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace("&", "&amp;") \
        .replace('"', "&quot;")
