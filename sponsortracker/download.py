import collections
import os
import shutil
import tempfile
from enum import Enum
from os.path import exists, expanduser, join, splitext

from sponsortracker import model, uploads
from sponsortracker.data import AssetType


ZIPNAME = "sponsortracker-assets"

def all(level=None):
    return download(level=level)

def website_updates(start):
    asset_filter = lambda deal: [asset for asset in deal.assets_by_type[AssetType.LOGO] if asset.date >= start]
    return download('updates', asset_filter=asset_filter)

def logo_cloud(level=None):
    asset_filter = lambda deal: deal.assets_by_type[AssetType.LOGO]
    return download('logocloud', by_sponsor=False, info=False, asset_filter=asset_filter, level=level)
    
def download(zipname=ZIPNAME, by_sponsor=True, info=True, asset_filter=lambda deal: deal.assets, level=None):
    with tempfile.TemporaryDirectory() as tempdir:
        zipdir = join(tempdir, zipname)
        os.makedirs(zipdir)
        
        for deal in model.Deal.query.filter(model.Deal.level_name != ""):
            if deal.level_name and deal.level_name == level:
                target = join(*[zipdir, deal.level.name.lower()] + ([deal.sponsor.name] if by_sponsor else []))
                os.makedirs(target, exist_ok=True)
                
                if info:
                    _info_to_file(target, deal.sponsor)
                _copy_assets(target, asset_filter(deal))
            
        return shutil.make_archive(expanduser(join("~", zipname)), "zip", root_dir=tempdir)

def _info_to_file(target, sponsor):
    if sponsor.link or sponsor.description:
        with open(join(target, "info.txt"), 'w') as info_file:
            if sponsor.link:
                info_file.write(sponsor.link + "\n\n")
            if sponsor.description:
                info_file.write(sponsor.description)

def _copy_assets(target, assets):
    for asset in assets:
        name = '-'.join([asset.deal.sponsor.name.lower(), asset.type.name.lower()])
        ext = splitext(asset.filename)[-1].lstrip('.')
        dest = os.path.join(target, "{name}.{ext}".format(name=name, ext=ext))
        uploads.Asset.get(asset.deal, asset.filename, dest)
        
        '''
        path = asset_uploader.path(asset.filename)
        ext = splitext(asset.filename)[-1].lstrip('.')
        name = '-'.join([asset.sponsor.name.lower(), asset.type.name.lower()])
        shutil.copy(path, _filepath(target, name, ext))
        '''
'''
def _filepath(target, basename, ext):
    num = 2
    name = "{name}.{ext}".format(name=basename, ext=ext)
    while exists(join(target, name)):
        name = "{name}_{num}.{ext}".format(name=basename, num=num, ext=ext)
        num += 1
    return join(target, name)
'''