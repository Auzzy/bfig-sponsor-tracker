from sponsortracker import model
from sponsortracker.data import AssetType, Level
from sponsortracker.assettracker import data, forms

def load_all_by_level():
    sponsors = [data.Sponsor.from_model(sponsor) for sponsor in model.Sponsor.query.all()]
    sponsors_by_level = {level:[] for level in Level}
    for sponsor in sponsors:
        if sponsor.level:
            sponsors_by_level[sponsor.level].append(sponsor)
    return sponsors_by_level

def load(id):
    return data.Sponsor.from_model(_load_model(id))

def _load_model(id, raise_404=True):
    get = "get_or_404" if raise_404 else "get"
    return getattr(model.Sponsor.query, get)(id)

def save_link(id, form):
    sponsor = _load_model(id)
    sponsor.info.link = form.link.data or ""
    model.db.session.commit()
    
def save_description(id, form):
    sponsor = _load_model(id)
    sponsor.info.description = form.description.data or ""
    model.db.session.commit()

def load_info(id):
    sponsor = load(id)
    return {info:sponsor.info.get(info) for info in data.InfoData}