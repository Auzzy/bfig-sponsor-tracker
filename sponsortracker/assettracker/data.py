import collections
import datetime
from enum import Enum

from sponsortracker import data
from sponsortracker.assettracker import forms
from sponsortracker.assettracker.app import asset_uploader, thumb_uploader

class InfoData(Enum):
    LINK = ("link", "Home Page", forms.LinkForm, "assettracker.info_link")
    DESCRIPTION = ("description", "Description", forms.DescriptionForm, "assettracker.info_description")
    
    def __init__(self, id, label, form_cls, view_name):
        self.id = id
        self.label = label
        self.form_cls = form_cls
        self.view_name = view_name
    
    @staticmethod
    def from_id(id):
        for info in InfoData:
            if info.id == id:
                return info
        return None

class Sponsor:
    INFO_LIST = [InfoData.LINK, InfoData.DESCRIPTION]
    
    def __init__(self, id, name, email, level, info, assets):
        self.id = id
        self.name = name
        self.email = email
        self.level = data.Level[level] if level else None
        self.info = info
        self.assets = assets
        
        if self.level:
            self.assets_by_type = collections.defaultdict(list)
            for asset in self.assets:
                self.assets_by_type[asset.type].append(asset)
            
            self.asset_type_by_date = {type:min(self.assets_by_type[type], key=lambda asset: asset.date) for type in self.assets_by_type}
            self.missing_assets = any(type not in self.assets_by_type for type in self.level.assets) or not self.info.link or not self.info.description
    
    @staticmethod
    def from_model(sponsor):
        info = Info.from_model(sponsor.info)
        assets = [Asset.from_model(asset) for asset in sponsor.assets]
        return Sponsor(sponsor.id, sponsor.name, sponsor.email, sponsor.level, info, assets)

class Info:
    def __init__(self, id, link, description):
        self.id = id
        self.link = link
        self.description = description
    
    @staticmethod
    def from_model(info):
        return Info(info.id, info.link, info.description)
    
    def get(self, info_data):
        if info_data == InfoData.LINK:
            return self.link
        elif info_data == InfoData.DESCRIPTION:
            return self.description
        return None

class Asset:
    def __init__(self, id, sponsor_id, date, type, filename):
        self.id = id
        self.sponsor_id = sponsor_id
        self.date = date
        self.type = data.AssetType[type]
        self.filename = filename
        self.url = asset_uploader.url(self.filename)
        self.thumbnail_url = thumb_uploader.url(self.filename)
    
    @staticmethod
    def new(sponsor_id, type, filename):
        return Asset(None, sponsor_id, datetime.datetime.today().date(), type, filename)
    
    @staticmethod
    def from_model(asset):
        return Asset(asset.id, asset.sponsor_id, asset.date, asset.type, asset.filename)
    
    def to_model(self, id=None):
        from sponsortracker import model
        self.id = self.id or id or None
        if self.id:
            asset_model = model.Asset.query.get(self.id)
            asset_model.update(type=self.type, date=self.date, filename=self.filename)
            return asset_model
        else:
            return model.Asset(self.sponsor_id, self.date, self.type.name, self.filename)