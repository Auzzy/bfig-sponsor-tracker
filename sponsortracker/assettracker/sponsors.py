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

def save_info(id, form):
    sponsor = model.Sponsor.query.get(id)
    if hasattr(form, "link"):
        sponsor.info.link = form.link.data or ""
    if hasattr(form, "description"):
        sponsor.info.description = form.description.data or ""
    model.db.session.commit()

def load_info(id):
    sponsor = model.Sponsor.query.get(id)
    return (
        forms.LinkForm(link=sponsor.info.link) if sponsor.info.link else forms.LinkForm(),
        forms.DescriptionForm(description=sponsor.info.description) if sponsor.info.description else forms.DescriptionForm()
    )