from flask.ext.user import SQLAlchemyAdapter, UserManager
from flask.ext.mail import Mail

from sponsortracker.app import app

app.config.from_object("sponsortracker.settings")

from sponsortracker.assettracker.app import asset_tracker
from sponsortracker.dealtracker.app import deal_tracker
from sponsortracker import views, model
from sponsortracker.usermodel import User, UserAuth

app.register_blueprint(asset_tracker, url_prefix="/assettracker")
app.register_blueprint(deal_tracker, url_prefix="/dealtracker")

mail = Mail(app)