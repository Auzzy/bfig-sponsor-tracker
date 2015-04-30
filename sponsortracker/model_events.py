import collections
import datetime

from flask.ext.sqlalchemy import event

from sponsortracker import data, model
from sponsortracker.dealtracker import uploads

_ASSET_REQUEST_OVERDUE_DAYS = 14
_CONTRACT_OVERDUE_DAYS = 14
_INVOICE_OVERDUE_DAYS = 14


# This solves SQLAlchemy's lack of an event for "after the constructor completes". The "init" event occurs upon
# constructor invocation, before the constructor is run, so no values are in place yet. The "load" event only occurs
# when data was constructed directly via the __new__ method, which appears to only be when it's loaded from the DB.
# But the "after_insert" event, although not at the desired level (Instance Level), provides an object which has been
# fully initialized.
# 
# Note that this means the session is already flushing, hence the lack of cross-table relationship references.
def init_and_load(cls):
    def register(func):
        event.listen(cls, 'load', lambda target, context: func(target))
        event.listen(cls, 'after_insert', lambda mapper, connection, target: func(target))
    return register

@init_and_load(model.Sponsor)
def load_sponsor(target):
    # For use by the views and controllers - not in the DB
    for deal in model.Deal.query.filter_by(sponsor_id=target.id):
        if deal.year == datetime.datetime.today().year:
            target.current = deal
            break
    else:
        deal = model.Deal(target.id, datetime.datetime.today().year)
        target.deals.append(deal)
        target.current = deal
    
    target.type = data.SponsorType[target.type_name] if target.type_name else None

@init_and_load(model.Deal)
def load_deal(target):
    user_auth = model.UserAuth.query.filter_by(username=target.owner).first()
    if user_auth:
        target.owner_name = "{user.first_name} {user.last_name}".format(user=user_auth.user)
    else:
        target.owner_name = target.owner
    
    target.assets_by_type = collections.defaultdict(list)
    for asset in model.Asset.query.filter_by(deal_id=target.id):
        target.assets_by_type[asset.type].append(asset)
            
    target.received_assets = True
    target.level = data.Level[target.level_name] if target.level_name else None
    if target.level:
        target.received_assets = all(type in target.assets_by_type for type in target.level.assets) and target.link and target.description

@init_and_load(model.Contract)
def load_contract(target):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_CONTRACT_OVERDUE_DAYS)
    else:
        target.overdue = None

@init_and_load(model.Invoice)
def load_invoice(target):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_INVOICE_OVERDUE_DAYS)
    else:
        target.overdue = None

@init_and_load(model.AssetRequest)
def load_asset_request(target):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_ASSET_REQUEST_OVERDUE_DAYS)
    else:
        target.overdue = None

@init_and_load(model.Asset)
def load_asset(target):
    # For use by the views and controllers - not in the DB
    target.type = data.AssetType[target.type_name]
    # target.url = asset_uploader.url(target.filename)
    # target.thumbnail_url = thumb_uploader.url(target.filename)
    target.url = uploads.Asset.url(target.deal, target.filename)
    target.thumbnail_url = uploads.Thumbnail.url(target.deal, target.filename)
    target.name = target.filename.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]

@init_and_load(model.User)
def load_user(target):
    target.type = data.UserType[target.type_name] if target.type_name in data.UserType.__members__ else None