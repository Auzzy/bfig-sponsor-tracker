from sponsortracker.app import app

app.config.from_object("sponsortracker.settings")

from sponsortracker.assettracker.app import asset_tracker
from sponsortracker.dealtracker.app import deal_tracker
from sponsortracker import views, model

app.register_blueprint(asset_tracker, url_prefix="/assettracker")
app.register_blueprint(deal_tracker, url_prefix="/dealtracker")
