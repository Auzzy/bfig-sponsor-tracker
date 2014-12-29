from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.user import SQLAlchemyAdapter, UserManager

from sponsortracker import data
from sponsortracker.app import app

db = SQLAlchemy(app)

from sponsortracker.usermodel import User, UserEmail, UserAuth, Role, UserRoles, init as init_usermodel, _init_data as _init_usermodel_data

db_adapter, user_manager = init_usermodel(app)

_ASSET_TYPES = [asset_type.name for asset_type in data.AssetType]

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True)
    email = db.Column(db.String(80), nullable=False)
    level = db.Column(db.String(16))
    cash = db.Column(db.Integer)
    inkind = db.Column(db.Integer)
    info = db.relationship("Info", uselist=False, backref="sponsor", cascade="all, delete-orphan", passive_updates=False)
    assets = db.relationship("Asset", cascade="all, delete-orphan", passive_updates=False)
    requests = db.relationship("Requests", uselist=False, backref="sponsor")
    
    def __init__(self, name, email, level=None, cash=None, inkind=None):
        self.name = name
        self.email = email
        self.level = level
        self.cash = cash
        self.inkind = inkind
        self.info = Info(self.id)
    
    def update(self, name=None, email=None, level=None, cash=None, inkind=None):
        self.name = name or self.name
        self.email = email or self.email
        self.level = level or self.level
        self.cash = cash or self.cash
        self.inkind = inkind or self.inkind

class Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    link = db.Column(db.String(120))
    description = db.Column(db.Text())
    
    def __init__(self, sponsor_id, link=None, description=None):
        self.sponsor_id = sponsor_id
        self.link = link
        self.description = description

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    date = db.Column(db.Date)
    type = db.Column(db.Enum(name="AssetType", *_ASSET_TYPES), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    
    def __init__(self, sponsor_id, date, type, filename):
        self.sponsor_id = sponsor_id
        self.date = date
        self.type = type
        self.filename = filename
    
    def update(self, sponsor_id=None, date=None, type=None, filename=None):
        self.sponsor_id = sponsor_id or self.sponsor_id
        self.date = date or self.date
        self.type = type or self.type
        self.filename = filename or self.filename

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


if not db.engine.table_names():
    db.create_all()
    _init_usermodel_data()