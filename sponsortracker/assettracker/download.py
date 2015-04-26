import collections
import os
import shutil
import tempfile
from enum import Enum
from os.path import exists, expanduser, join, splitext

from sponsortracker import data, model
from sponsortracker.dealtracker.app import asset_uploader

ZIPNAME = "sponsortracker-assets"

def all():
    return download()

def website_updates(start):
    asset_filter = lambda sponsor: [asset for asset in sponsor.current.assets_by_type[data.AssetType.LOGO] if asset.date >= start]
    return download('updates', asset_filter=asset_filter)

def logo_cloud():
    asset_filter = lambda sponsor: sponsor.current.assets_by_type[data.AssetType.LOGO]
    return download('logocloud', by_sponsor=False, info=False, asset_filter=asset_filter)
    
def download(zipname=ZIPNAME, by_sponsor=True, info=True, asset_filter=lambda sponsor: sponsor.current.assets):
    with tempfile.TemporaryDirectory() as tempdir:
        zipdir = join(tempdir, zipname)
        os.makedirs(zipdir)
        
        for sponsor in model.Sponsor.query.filter(model.Deal.level_name != ""):
            target = join(*[zipdir, sponsor.current.level.name.lower()] + ([sponsor.name] if by_sponsor else []))
            os.makedirs(target, exist_ok=True)
            
            if info:
                _info_to_file(target, sponsor)
            _copy_assets(target, asset_filter(sponsor))
        
        return shutil.make_archive(expanduser(join("~", zipname)), "zip", root_dir=tempdir)

def _info_to_file(target, sponsor):
    if sponsor.link or sponsor.description:
        with open(join(target, "info.txt"), 'w') as info_file:
            data = [sponsor.link, sponsor.description]
            info_file.write("\n\n".join([field for field in data if field]))

def _copy_assets(target, assets):
    for asset in assets:
        path = asset_uploader.path(asset.filename)
        ext = splitext(asset.filename)[-1].lstrip('.')
        name = '-'.join([asset.deal.sponsor.name.lower(), asset.type.name.lower()])
        shutil.copy(path, _filepath(target, name, ext))

def _filepath(target, basename, ext):
    num = 2
    name = "{name}.{ext}".format(name=basename, ext=ext)
    while exists(join(target, name)):
        name = "{name}_{num}.{ext}".format(name=basename, num=num, ext=ext)
        num += 1
    return join(target, name)
