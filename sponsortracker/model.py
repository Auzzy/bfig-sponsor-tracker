import collections
import datetime
import re

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager
from flask.ext.sqlalchemy import event, SQLAlchemy
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

_ASSET_REQUEST_OVERDUE_DAYS = 14
_CONTRACT_OVERDUE_DAYS = 14
_INVOICE_OVERDUE_DAYS = 14


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
        
        load_sponsor(self, None)
        
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
        
        load_deal(self, None)
    
    def update_values(self, year=None, owner=None, cash=None, inkind=None, level_name=None):
        self.year = year or self.year
        self.owner = self._update_field(self.owner, owner)
        self.cash = self._update_field(self.cash, cash)
        self.inkind = self._update_field(self.inkind, inkind)
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
        
        load_contract(self, None)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    ready = db.Column(db.Boolean)
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, ready=False, sent=None, received=None):
        super(Invoice, self).__init__()
        
        self.deal_id = deal_id
        self.ready = ready
        self.sent = sent
        self.received = received
        
        load_invoice(self, None)

class AssetRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    ready = db.Column(db.Boolean)
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, ready=False, sent=None, received=None):
        super(AssetRequest, self).__init__()
        
        self.deal_id = deal_id
        self.ready = ready
        self.sent = sent
        self.received = received
        
        load_asset_request(self, None)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    date = db.Column(db.Date)
    type_name = db.Column("type", db.Enum(name="AssetType", native_enum=False, *_ASSET_TYPES), nullable=False)
    filename = db.Column(db.String(256), nullable=False)
    usages = db.Column(db.Integer, nullable=False, default=0)
    
    def __init__(self, deal_id, type_name, filename, date=datetime.datetime.today().date(), usages=0):
        super(Asset, self).__init__()
        
        self.date = date
        self.type_name = type_name
        self.filename = filename
        self.deal_id = deal_id
        self.usages = usages
        
        load_asset(self, None)
    
    def update_values(self, deal_id=None, date=None, type_name=None, filename=None):
        self.deal_id = deal_id or self.deal_id
        self.date = date or self.date
        self.type_name = type_name or self.type_name
        self.filename = filename or self.filename
    
    def increment_usage(self):
        self.usages += 1
    
    def decrement_usage(self):
        if self.usages >= 1:
            self.usages -= 1
    
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    type_name = db.Column(db.Enum(name="UserType", native_enum=False, *_USER_TYPES), nullable=False)
    emails = db.relationship("UserEmail", lazy="dynamic")
    user_auth = db.relationship("UserAuth", uselist=False)
    
    def update_values(self, type_name, first_name, last_name, email, username):
        self.type_name = type_name or self.type_name
        self.first_name = first_name or self.first_name
        self.last_name = last_name or self.last_name
        
        self.user_auth.username = username or self.user_auth.username
        
        if not self.emails.filter_by(email=email).all():
            email = model.UserEmail(email=email, is_primary=True)
            self.emails = [email]
    
    def _update_field(self, old_value, new_value, cleared="", unset=None):
        if new_value is not unset:
            return unset if new_value == cleared else new_value
        return old_value
    
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


@event.listens_for(Sponsor, 'load')
def load_sponsor(target, context):
    # For use by the views and controllers - not in the DB
    for deal in target.deals:
        if deal.year == datetime.datetime.today().year:
            target.current = deal
            break
    else:
        deal = Deal(target.id, datetime.datetime.today().year)
        target.deals.append(deal)
        target.current = deal
    
    target.type = data.SponsorType[target.type_name] if target.type_name else None

@event.listens_for(Deal, 'load')
def load_deal(target, context):
    user_auth = UserAuth.query.filter_by(username=target.owner).first()
    if user_auth:
        target.owner_name = "{user.first_name} {user.last_name}".format(user=user_auth.user)
    else:
        target.owner_name = target.owner
    
    target.assets_by_type = collections.defaultdict(list)
    for asset in target.assets:
        target.assets_by_type[asset.type].append(asset)
            
    target.received_assets = True
    target.level = data.Level[target.level_name] if target.level_name else None
    if target.level:
        target.received_assets = all(type in target.assets_by_type for type in target.level.assets)

@event.listens_for(Contract, 'load')
def load_contract(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_CONTRACT_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(Invoice, 'load')
def load_invoice(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_INVOICE_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(AssetRequest, 'load')
def load_asset_request(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_ASSET_REQUEST_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(Asset, 'load')
def load_asset(target, context):
    # For use by the views and controllers - not in the DB
    target.name = target.filename.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]
    target.type = data.AssetType[target.type_name]


@event.listens_for(User, 'load')
def load_user(target, context):
    target.type = data.UserType[target.type_name] if target.type_name in data.UserType.__members__ else None



def password_validator(form, field):
    password = field.data
    if len(password) < 6:
        raise ValidationError("Password must have at least 6 characters.")

if not hasattr(app, "user_manager"):
    db_adapter = SQLAlchemyAdapter(db, User, UserAuthClass=UserAuth, UserEmailClass=UserEmail)
    user_manager = UserManager(db_adapter, app, password_validator=password_validator)


if __name__ == '__main__':
    manager.run()
