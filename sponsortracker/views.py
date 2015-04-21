from flask import redirect, render_template, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sponsortracker.app import app
from sponsortracker.data import UserType

@app.route("/")
@login_required
def home():
    if current_user.type in (UserType.SALES, UserType.SALES_ADMIN):
        return redirect(url_for("dealtracker.all"))
    elif current_user.type in (UserType.MARKETING, UserType.MARKETING_ADMIN):
        return redirect(url_for("assettracker.home"))
    else:
        return render_template("home.html")