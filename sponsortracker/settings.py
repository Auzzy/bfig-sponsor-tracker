import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "sponsortracker.db")
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, "db_repository")

WTF_CSRF_ENABLED = True
SECRET_KEY = "e211788b-355d-4da4-844c-d7a244992a43"

UPLOADS_DEFAULT_DEST = os.path.join(basedir, "uploads")