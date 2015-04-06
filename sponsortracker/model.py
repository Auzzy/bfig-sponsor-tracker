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
from sponsortracker.assettracker.app import asset_uploader, thumb_uploader

db = SQLAlchemy(app)
migrate = Migrate(app, db, directory=app.config["MIGRATIONS_DIRECTORY"])
manager = Manager(app)
manager.add_command('db', MigrateCommand)


_ASSET_TYPES = [asset_type.name for asset_type in data.AssetType]
_LEVEL_TYPES = [level.name for level in data.Level]
_SPONSOR_TYPES = [sponsor_type.name for sponsor_type in data.SponsorType]
_USER_TYPES = [user_type.type for user_type in data.UserType]
_CONTRACT_OVERDUE_DAYS = 14
_INVOICE_OVERDUE_DAYS = 14

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

class Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    link = db.Column(db.String(2000))
    description = db.Column(db.Text())
    
    def __init__(self, sponsor_id, link=None, description=None):
        self.sponsor_id = sponsor_id
        self.link = link
        self.description = description

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

class Deal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    year = db.Column(db.Integer)
    owner = db.Column(db.String(60))
    cash = db.Column(db.Integer)
    inkind = db.Column(db.Integer)
    contract = db.relationship("Contract", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="deal")
    invoice = db.relationship("Invoice", uselist=False, cascade="all, delete-orphan", passive_updates=False, backref="deal")
    
    def __init__(self, sponsor_id, year, owner=None, cash=0, inkind=0):
        self.sponsor_id = sponsor_id
        self.year = year
        self.owner = owner
        self.cash = cash
        self.inkind = inkind
    
    def update(self, year=None, owner=None, cash=None, inkind=None):
        self.year = year or self.year
        self.owner = owner or self.owner
        self.cash = cash if cash is not None else self.cash
        self.inkind = inkind if inkind is not None else self.inkind
    
    def init_contract_invoice(self):
        if not self.contract:
            self.contract = Contract(self.id)
        if not self.invoice:
            self.invoice = Invoice(self.id)
    
    def remove_contract_invoice(self):
        if self.contract:
            db.session.delete(self.contract)
        if self.invoice:
            db.session.delete(self.invoice)
        db.session.commit()

class Contract(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, sent=None, received=None):
        self.deal_id = deal_id
        self.sent = sent
        self.received = received

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    deal_id = db.Column(db.Integer, db.ForeignKey('deal.id'))
    sent = db.Column(db.Date)
    received = db.Column(db.Date)
    
    def __init__(self, deal_id, sent=None, received=None):
        self.deal_id = deal_id
        self.sent = sent
        self.received = received


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



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    type = db.Column(db.Enum(name="UserType", *_USER_TYPES), nullable=False)
    emails = db.relationship("UserEmail")
    roles = db.relationship("Role", secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    user_auth = db.relationship("UserAuth", uselist=False)
    
    def is_active(self):
        return self.enabled
    
    def has_roles(self, *roles):
        return super(User, self).has_roles(*data.RoleType.types(roles))

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

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(50), unique=True)
    
    def __getattr__(self, name):
        if name == "name":
            return self.type
        return super(Role, self).__getattr__(self, name)
    
class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("role.id", ondelete="CASCADE"))


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

@event.listens_for(Asset, 'load')
def load_asset(target, context):
    # For use by the views and controllers - not in the DB
    target.type = data.AssetType[target.type_name]
    target.url = asset_uploader.url(target.filename)
    target.thumbnail_url = thumb_uploader.url(target.filename)
    target.name = target.filename.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]

@event.listens_for(User.type, 'set')
def handle_type_change(user, type, old_type, initiator):
    if type != old_type:
        roles = data.UserType.from_type(type).roles
        role_types = data.RoleType.types(roles)
        user.roles = Role.query.filter(Role.type.in_(role_types)).all()


def password_validator(form, field):
    password = field.data
    if len(password) < 6:
        raise ValidationError("Password must have at least 6 characters.")


if not hasattr(app, "user_manager"):
    db_adapter = SQLAlchemyAdapter(db, User, UserAuthClass=UserAuth, UserEmailClass=UserEmail)
    user_manager = UserManager(db_adapter, app, password_validator=password_validator)


if __name__ == '__main__':
    manager.run()
