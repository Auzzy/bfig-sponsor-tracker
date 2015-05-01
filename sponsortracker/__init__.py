from flask.ext.user import SQLAlchemyAdapter, UserManager

from sponsortracker.app import app
# from sponsortracker.assettracker.app import asset_tracker
from sponsortracker.dealtracker.app import deal_tracker
# from sponsortracker import model, model_events, views
from sponsortracker import model, views

# app.register_blueprint(asset_tracker, url_prefix="/assettracker")
app.register_blueprint(deal_tracker, url_prefix="/dealtracker")
