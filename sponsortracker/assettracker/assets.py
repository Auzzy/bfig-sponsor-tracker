from sponsortracker import model
from sponsortracker.assettracker import data, sponsors

def save(sponsor_id, form):
    asset_model = data.Asset.from_form(form, sponsor_id).to_model()
    model.db.session.add(asset_model)
    model.db.session.commit()
