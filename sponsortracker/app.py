from flask import Flask
from flask.ext.mail import Mail
from flask.ext.wtf.csrf import CsrfProtect

app = Flask(__name__)

csrf = CsrfProtect(app)
mail = Mail(app)