from flask.ext.user import login_required
from flask.ext.login import logout_user

from sponsortracker.app import app 

@app.route("/")
@login_required
def home():
    logout_user()
    return "Main page"