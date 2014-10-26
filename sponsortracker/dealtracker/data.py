from sponsortracker import data

class Sponsor:
    def __init__(self, id, name, email, level, cash, inkind):
        self.id = id
        self.name = name
        self.email = email
        self.level = data.Level[level] if level else None
        self.cash = cash
        self.inkind = inkind
    
    @staticmethod
    def from_model(model):
        return Sponsor(model.id, model.name, model.email, model.level, model.cash, model.inkind)
    
    @staticmethod
    def from_form(form):
        return Sponsor(None, form.name.data, form.email.data, form.level.data, form.cash.data, form.inkind.data)
    
    def to_model(self, id=None):
        from sponsortracker import model
        level = self.level.name if self.level else ""
        self.id = self.id or id or None
        if self.id:
            sponsor_model = model.Sponsor.query.get(self.id)
            sponsor_model.update(name=self.name, email=self.email, level=level, cash=self.cash, inkind=self.inkind)
            return sponsor_model
        else:
            return model.Sponsor(self.name, self.email, level, self.cash, self.inkind)
        
    def to_form(self):
        from sponsortracker.dealtracker import forms
        level = self.level.name if self.level else ""
        return forms.SponsorForm(name=self.name, email=self.email, level=level, cash=self.cash, inkind=self.inkind)