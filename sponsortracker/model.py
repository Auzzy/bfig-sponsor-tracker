import collections
import datetime
import re

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import SQLAlchemyAdapter, UserManager, UserMixin
from wtforms.validators import ValidationError

from sponsortracker import data
from sponsortracker.app import app

db = SQLAlchemy(app)
migrate = Migrate(app, db, directory=app.config["MIGRATIONS_DIRECTORY"])
manager = Manager(app)
manager.add_command('db', MigrateCommand)


_ASSET_TYPES = [asset_type.name for asset_type in data.AssetType]
_LEVEL_TYPES = [level.name for level in data.Level]
_SPONSOR_TYPES = [sponsor_type.name for sponsor_type in data.SponsorType]
_USER_TYPES = [user_type.name for user_type in data.UserType]

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    type_name = db.Column("type", db.Enum(name="SponsorType", native_enum=False, *_SPONSOR_TYPES))
    notes = db.Column(db.Text())
    link = db.Column(db.String(2000))
    description = db.Column(db.Text())
    contacts = db.relationship("Contact", cascade="all, delete-orphan", passive_updates=False, backref="sponsor", lazy="dynamic")
    deals = db.relationship("Deal", cascade="all, delete-orphan", passive_updates=False, backref="sponsor", lazy="dynamic")
    
    def __init__(self, name, type_name=None, notes=None, link=None, description=None):
        super(Sponsor, self).__init__()
        
        self.name = name
        self.type_name = type_name or None
        self.notes = notes
        self.link = link
        self.description = description
        
    def update_values(self, name=None, type_name=None, notes=None, link=None, description=None):
        self.name = name or self.name
        self.type_name = self._update_field(self.type_name, type_name)
        self.notes = self._update_field(self.notes, notes)
        self.link = self._update_field(self.link, link)
        self.description = self._update_field(self.description, description)
    
    def _update_field(self, old_value, new_value, cleared=""):
        if new_value is not None:
            return None if new_value == cleared else new_value
        return old_value
    
    def set_contacts(self, contact_email_name):
        contacts = []
        for email,name in contact_email_name:
            contact = Contact.query.filter_by(email=email).first()
            if contact:
                contact.update_values(name=name)
            else:
                contact = Contact(self.id, email, name)
            contacts.append(contact)
        self.contacts = contacts
    
    def add_deal(self, year, owner=None, cash=0, inkind=0):
        if not year:
            return None
        
        for deal in self.deals:
            if deal.year == year:
                deal.update_values(owner=owner, cash=cash, inkind=inkind)
                break
        else:
            deal = Deal(self.id, year, owner, cash, inkind)
            self.deals.append(deal)
        return deal

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    email = db.Column(db.String(80))
    name = db.Column(db.String(40))
    
    def __init__(self, sponsor_id, email, name=None):
        super(Contact, self).__init__()
        
        self.sponsor_id = sponsor_id
        self.email = email
        self.name = email.split('@')[0] if not name and email and '@' in email else name
    
    def update_values(self, email=None, name=None):
        self.email = self._update_field(self.email, email)
        self.name = self._update_field(self.name, name)
        
    def _update_field(self, old_value, new_value, cleared=""):
        if new_value is not None:
            return None if new_value == cleared else new_value
        return old_value

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    year = db.Column(db.Integer)
    owner = db.Column(db.String(60))
    cash = db.Column(db.Integer)
    inkind = db.Column(db.Integer)
    level_name = db.Column("level", db.Enum(name="LevelType", native_enum=False, *_LEVEL_TYPES))
    contract = db.relationship("Contract", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="deal")
    invoice = db.relationship("Invoice", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="deal")
    asset_request = db.relationship("AssetRequest", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="deal")
    assets = db.relationship("Asset", cascade="all, delete-orphan", passive_updates=False, backref="deal", lazy="dynamic")
    
    def __init__(self, sponsor_id, year, owner=None, cash=0, inkind=0, level_name=None):
        super(Deal, self).__init__()
        
        self.sponsor_id = sponsor_id
        self.year = year
        self.owner = owner
        self.cash = cash
        self.inkind = inkind
        self.level_name = level_name
        
        self.contract = Contract(self.id)
        self.invoice = Invoice(self.id)
        self.asset_request = AssetRequest(self.id)
    
    def update_values(self, year=None, owner=None, cash=0, inkind=0, level_name=None):
        self.year = year or self.year
        self.owner = self._update_field(self.owner, owner)
        self.cash = self._update_field(self.cash, cash, None, 0)
        self.inkind = self._update_field(self.inkind, inkind, None, 0)
        self.level_name = self._update_field(self.level_name, level_name)
    
    def _update_field(self, old_value, new_value, cleared="", unset=None):
        if new_value is not unset:
            return unset if new_value == cleared else new_value
        return old_value

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    ready = db.Column(db.Boolean, default=False)
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, ready=False, sent=None, received=None):
        super(Contract, self).__init__()
        
        self.deal_id = deal_id
        self.ready = ready
        self.sent = sent
        self.received = received

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    ready = db.Column(db.Boolean, default=False)
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, ready=False, sent=None, received=None):
        super(Invoice, self).__init__()
        
        self.deal_id = deal_id
        self.ready = ready
        self.sent = sent
        self.received = received

class AssetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    ready = db.Column(db.Boolean, default=False)
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, ready=False, sent=None, received=None):
        super(AssetRequest, self).__init__()
        
        self.deal_id = deal_id
        self.ready = ready
        self.sent = sent
        self.received = received

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    date = db.Column(db.Date)
    type_name = db.Column("type", db.Enum(name="AssetType", native_enum=False, *_ASSET_TYPES), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    
    def __init__(self, deal_id, type_name, filename, date=datetime.datetime.today().date()):
        super(Asset, self).__init__()
        
        self.deal_id = deal_id
        self.date = date
        self.type_name = type_name
        self.filename = filename
    
    def update_values(self, deal_id=None, date=None, type_name=None, filename=None):
        self.deal_id = deal_id or self.deal_id
        self.date = date or self.date
        self.type_name = type_name or self.type_name
        self.filename = filename or self.filename        

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    type_name = db.Column(db.Enum(name="UserType", native_enum=False, *_USER_TYPES), nullable=False)
    emails = db.relationship("UserEmail", lazy="dynamic")
    user_auth = db.relationship("UserAuth", uselist=False)
    
    def is_active(self):
        return self.enabled

class UserEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(255), nullable=False, unique=True)
    is_primary = db.Column(db.Boolean(), nullable=False, default=False)
    confirmed_at = db.Column(db.DateTime())
    user = db.relationship('User', uselist=False)

class UserAuth(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, default='')
    reset_password_token = db.Column(db.String(100), nullable=False, default='')
    user = db.relationship('User', uselist=False, foreign_keys=user_id)
    

def password_validator(form, field):
    password = field.data
    if len(password) < 6:
        raise ValidationError("Password must have at least 6 characters.")

if not hasattr(app, "user_manager"):
    db_adapter = SQLAlchemyAdapter(db, User, UserAuthClass=UserAuth, UserEmailClass=UserEmail)
    user_manager = UserManager(db_adapter, app, password_validator=password_validator)


if __name__ == '__main__':
    manager.run()
