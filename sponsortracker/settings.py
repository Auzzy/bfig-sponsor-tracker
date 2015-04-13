import os
basedir = os.path.abspath(os.path.dirname(__file__))

PROPAGATE_EXCEPTIONS = True

# Flask-SQLAlchemy
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "postgresql:///sponsortracker")

# Flask-WTForms
WTF_CSRF_ENABLED = True
SECRET_KEY = "e211788b-355d-4da4-844c-d7a244992a43"

# Flask-Uploads
UPLOADS_DEFAULT_DEST = os.path.join(basedir, "uploads")

# Flask-Users
USER_APP_NAME = "Sponsor Tracker"
USER_ENABLE_CHANGE_USERNAME = False
USER_ENABLE_REGISTRATION = False
USER_ENABLE_CONFIRM_EMAIL = False
USER_ENABLE_FORGOT_PASSWORD = True

# Flask-Mail
MAIL_USERNAME = "sponsors@bostonfig.com"
MAIL_PASSWORD = "2015bfig!"
MAIL_DEFAULT_SENDER = ("Boston FIG Sponsor Coordinator", "sponsors@bostonfig.com")
DEFAULT_MAIL_SENDER = ("Boston FIG Sponsor Coordinator", "sponsors@bostonfig.com")
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
MAIL_USE_SSL = True

# Custom
MIGRATIONS_DIRECTORY = "migrations"
