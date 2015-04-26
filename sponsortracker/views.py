from flask import redirect, render_template, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sponsortracker.app import app
from sponsortracker.data import UserType

@app.route("/")
@login_required
def home():
    return redirect(url_for("dealtracker.all"))