import collections
import datetime

from flask.ext.sqlalchemy import event

from sponsortracker import data, model
from sponsortracker.dealtracker import uploads

_ASSET_REQUEST_OVERDUE_DAYS = 14
_CONTRACT_OVERDUE_DAYS = 14
_INVOICE_OVERDUE_DAYS = 14


@event.listens_for(model.Sponsor, 'load')
def load_sponsor(target, context):
    # For use by the views and controllers - not in the DB
    for deal in target.deals:
        if deal.year == datetime.datetime.today().year:
            target.current = deal
            break
    else:
        deal = model.Deal(target.id, datetime.datetime.today().year)
        target.deals.append(deal)
        target.current = deal
    
    target.type = data.SponsorType[target.type_name] if target.type_name else None

@event.listens_for(model.Deal, 'load')
def load_deal(target, context):
    user_auth = model.UserAuth.query.filter_by(username=target.owner).first()
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
        target.received_assets = all(type in target.assets_by_type for type in target.level.assets) and target.link and target.description

@event.listens_for(model.Contract, 'load')
def load_contract(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_CONTRACT_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(model.Invoice, 'load')
def load_invoice(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_INVOICE_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(model.AssetRequest, 'load')
def load_asset_request(target, context):
    if target.sent:
        target.overdue = target.sent <= datetime.date.today() - datetime.timedelta(days=_ASSET_REQUEST_OVERDUE_DAYS)
    else:
        target.overdue = None

@event.listens_for(model.Asset, 'load')
def load_asset(target, context):
    # For use by the views and controllers - not in the DB
    target.type = data.AssetType[target.type_name]
    # target.url = asset_uploader.url(target.filename)
    # target.thumbnail_url = thumb_uploader.url(target.filename)
    target.url = uploads.Asset.url(target.deal, target.filename)
    target.thumbnail_url = uploads.Thumbnail.url(target.deal, target.filename)
    target.name = target.filename.rsplit('/', maxsplit=1)[-1].rsplit('.', maxsplit=1)[0]

@event.listens_for(model.User, 'load')
def load_user(target, context):
    target.type = data.UserType[target.type_name] if target.type_name in data.UserType.__members__ else None
