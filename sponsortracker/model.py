import collections
import datetime
import re

from flask.ext.sqlalchemy import event, SQLAlchemy
from flask.ext.user import SQLAlchemyAdapter, UserManager

from sponsortracker import data
from sponsortracker.app import app
from sponsortracker.assettracker.app import asset_uploader, thumb_uploader

db = SQLAlchemy(app)

from sponsortracker.usermodel import User, UserEmail, UserAuth, Role, UserRoles, init as init_usermodel, _init_data as _init_usermodel_data

db_adapter, user_manager = init_usermodel(app)

_ASSET_TYPES = [asset_type.name for asset_type in data.AssetType]
_LEVEL_TYPES = [level.name for level in data.Level]
_SPONSOR_TYPES = [sponsor_type.name for sponsor_type in data.SponsorType]

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    type_name = db.Column("type", db.Enum(name="SponsorType", *_SPONSOR_TYPES))
    level_name = db.Column("level", db.Enum(name="LevelType", *_LEVEL_TYPES))
    notes = db.Column(db.Text())
    info = db.relationship("Info", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="sponsor")
    contacts = db.relationship("Contact", cascade="all, delete-orphan", passive_updates=False, backref="sponsor")
    assets = db.relationship("Asset", cascade="all, delete-orphan", passive_updates=False, backref="sponsor")
    deals = db.relationship("Deal", cascade="all, delete-orphan", passive_updates=False, backref="sponsor")
    # requests = db.relationship("Requests", uselist=False, backref="sponsor")
    
    def __init__(self, name, type_name=None, level_name=None, notes=None):
        self.name = name
        self.type_name = type_name or None
        self.level_name = level_name or None
        self.notes = notes
        self.info = Info(self.id)
        
        self.deals.append(Deal(self.id, datetime.date.today().year))
        self.current = self.deals[0]
        
        load_sponsor(self, None)
        
    def update(self, name=None, type_name=None, level_name=None, notes=None):
        self.name = name or self.name
        self.type_name = type_name or self.type_name
        self.level_name = level_name or self.level_name
        
        self.notes = notes or self.notes
    
    def save_link(self, form):
        self.info.link = form.link.data or ""
        db.session.commit()
        
    def save_description(self, form):
        self.info.description = form.description.data or ""
        db.session.commit()
    
    def add_contact(self, email, name=None):
        if not email:
            return None
        
        contact = Contact.query.filter_by(sponsor_id=self.id, email=email).first()
        if contact:
            contact.update(name=name)
        else:
            contact = Contact(self.id, email, name)
            self.contacts.append(contact)
        return contact
    
    def add_deal(self, year, owner=None, cash=0, inkind=0):
        if not year:
            return None
        
        deal = Deal.query.filter_by(sponsor_id=self.id, year=year).first()
        if deal:
            deal.update(owner=owner, cash=cash, inkind=inkind)
        else:
            deal = Deal(self.id, year, owner, cash, inkind)
            self.deals.append(deal)
        return deal

@event.listens_for(Sponsor, 'load')
def load_sponsor(target, context):
    # For use by the views and controllers - not in the DB
    target.current = target.deals[0]
    
    target.assets_by_type = {}
    target.received_assets = True
    target.type = data.SponsorType[target.type_name] if target.type_name else None
    target.level = data.Level[target.level_name] if target.level_name else None
    if target.level:
        target.assets_by_type = collections.defaultdict(list)
        for asset in target.assets:
            target.assets_by_type[asset.type].append(asset)
        
        target.received_assets = all(type in target.assets_by_type for type in target.level.assets) and target.info.link and target.info.description

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    email = db.Column(db.String(80))
    name = db.Column(db.String(40))
    
    def __init__(self, sponsor_id, email, name=None):
        self.sponsor_id = sponsor_id
        
        self.email = email
        self.name = email.split('@')[0] if not name and email and '@' in email else name
    
    def update(self, email=None, name=None):
        self.email = email or self.email
        self.name = name or self.name

class Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    link = db.Column(db.String(2000))
    description = db.Column(db.Text())
    
    def __init__(self, sponsor_id, link=None, description=None):
        self.sponsor_id = sponsor_id
        self.link = link
        self.description = description

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    date = db.Column(db.Date)
    type_name = db.Column("type", db.Enum(name="AssetType", *_ASSET_TYPES), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    
    def __init__(self, sponsor_id, type_name, filename, date=datetime.datetime.today().date()):
        self.sponsor_id = sponsor_id
        self.date = date
        self.type_name = type_name
        self.filename = filename
        
        load_asset(self, None)
    
    def update(self, sponsor_id=None, date=None, type=None, filename=None):
        self.sponsor_id = sponsor_id or self.sponsor_id
        self.date = date or self.date
        self.type = type or self.type
        self.filename = filename or self.filename

@event.listens_for(Asset, 'load')
def load_asset(target, context):
    # For use by the views and controllers - not in the DB
    target.type = data.AssetType[target.type_name]
    target.url = asset_uploader.url(target.filename)
    target.thumbnail_url = thumb_uploader.url(target.filename)
    target.name = target.filename.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    year = db.Column(db.Integer)
    owner = db.Column(db.String(60))
    cash = db.Column(db.Integer)
    inkind = db.Column(db.Integer)
    
    def __init__(self, sponsor_id, year, owner=None, cash=0, inkind=0):
        self.sponsor_id = sponsor_id
        self.year = year
        self.owner = owner
        self.cash = cash
        self.inkind = inkind
    
    def update(self, year=None, owner=None, cash=None, inkind=None):
        self.year = year or self.year
        self.owner = owner or self.owner
        self.cash = cash or self.cash
        self.inkind = inkind or self.inkind



'''
class Requests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    invoices = db.relationship("Invoice")
    assets = db.relationship("AssetRequest")

    def __init__(self, sponsor_id):
        self.sponsor_id = sponsor_id
    
class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requests_id = db.Column(db.Integer, db.ForeignKey('requests.id'))
    date = db.Column(db.Date, nullable=False)
    
    def __init__(self, request_id, date):
        self.request_id = request_id
        self.date = date

class AssetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    requests_id = db.Column(db.Integer, db.ForeignKey('requests.id'))
    date = db.Column(db.Date, nullable=False)
    
    def __init__(self, requests_id, date):
        self.requests_id = requests_id
        self.date = date
'''

if not db.engine.table_names():
    db.create_all()
    _init_usermodel_data()