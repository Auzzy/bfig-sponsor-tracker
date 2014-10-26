from sponsortracker import model
from sponsortracker.dealtracker import data

def configure(id, form):
    sponsor = data.Sponsor.from_form(form)
    if id:
        edit(id, sponsor)
    else:
        add(sponsor)

def add(sponsor):
    sponsor_model = sponsor.to_model()
    model.db.session.add(sponsor_model)
    model.db.session.commit()

def edit(id, sponsor):
    sponsor_model = sponsor.to_model(id)
    model.db.session.commit()
    
def load_all():
    return [data.Sponsor.from_model(sponsor) for sponsor in model.Sponsor.query.all()]

def load(id):
    return data.Sponsor.from_model(_load_model(id))
    
def _load_model(id, raise_404=True):
    get = "get_or_404" if raise_404 else "get"
    return getattr(model.Sponsor.query, get)(id)