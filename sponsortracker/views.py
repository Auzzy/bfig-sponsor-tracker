from flask import redirect, render_template, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sponsortracker.app import app
from sponsortracker.data import RoleType

@app.route("/")
@login_required
def home():
    if not current_user.has_roles((RoleType.AT_WRITE, RoleType.AT_READ), (RoleType.DT_WRITE, RoleType.DT_READ)):
        if current_user.has_roles((RoleType.AT_WRITE, RoleType.AT_READ)):
            return redirect(url_for("assettracker.home"))
        else:
            return redirect(url_for("dealtracker.home"))
    
    return render_template("home.html")