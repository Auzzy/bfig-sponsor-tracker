import os
basedir = os.path.abspath(os.path.dirname(__file__))

# Flask-SQLAlchemy
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', "sqlite:///" + os.path.join(basedir, "sponsortracker.db"))
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, "db_repository")

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
MAIL_USERNAME = "bfigtest@gmail.com"
MAIL_PASSWORD = "bfig-test"
MAIL_DEFAULT_SENDER = ("BFIG Test", "bfigtest@gmail.com")
DEFAULT_MAIL_SENDER = ("BFIG Test", "bfigtest@gmail.com")
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 465
# MAIL_PORT = 587
MAIL_USE_SSL = True
# MAIL_USE_TLS = True
