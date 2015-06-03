from flask import Flask
from flask.ext.mail import Mail
from flask.ext.wtf.csrf import CsrfProtect
from flaskext.uploads import UploadSet

from sponsortracker import data

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config.from_object("sponsortracker.settings")

csrf = CsrfProtect(app)
mail = Mail(app)

preview_uploader = UploadSet("previews", data.ASSET_FORMATS_EXT)