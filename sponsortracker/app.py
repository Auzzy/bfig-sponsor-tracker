from flask import Flask
from flask.ext.mail import Mail
from flask.ext.wtf.csrf import CsrfProtect

app = Flask(__name__)
app.config.from_object("sponsortracker.settings")

csrf = CsrfProtect(app)
mail = Mail(app)
