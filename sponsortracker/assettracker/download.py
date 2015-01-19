import os
import shutil
import tempfile
from os.path import exists, expanduser, join, splitext

from sponsortracker.data import AssetType
from sponsortracker.assettracker import sponsors
from sponsortracker.assettracker.app import asset_uploader

ZIPDIR = "sponsortracker-assets"

def all():
    def handle_sponsor(zipdir, sponsor):
        sponsordir = join(zipdir, sponsor.level.name.lower(), sponsor.name)
        os.makedirs(sponsordir)
        
        _info_to_file(sponsordir, sponsor.info)
        _copy_assets(sponsordir, sponsor.assets, basename=lambda asset: '-'.join([sponsor.name.lower(), asset.type.name.lower()]))
        
    return _zip_all(handle_sponsor)

def website_updates():
    pass

def logo_cloud():
    def handle_sponsor(zipdir, sponsor):
        leveldir = join(zipdir, sponsor.level.name.lower())
        os.makedirs(leveldir, exist_ok=True)
        
        logo_filter = [AssetType.LOGO]
        _copy_assets(leveldir, sponsor.assets, logo_filter, basename=lambda asset: sponsor.name.lower())
    
    return _zip_all(handle_sponsor, "sponsortracker-logo-cloud")


def _zip_all(handle_sponsor, name=None):
    with tempfile.TemporaryDirectory() as tempdir:
        zipdir = join(tempdir, ZIPDIR)
        os.makedirs(zipdir)
        
        for sponsor in sponsors.load_all():
            handle_sponsor(zipdir, sponsor)
        
        name = name or "sponsortracker-assets"
        return shutil.make_archive(expanduser(join("~", name)), "zip", root_dir=tempdir)

def _info_to_file(zipdir, info):
    if info.link or info.description:
        with open(join(zipdir, "info.txt"), 'w') as info_file:
            data = [info.link, info.description]
            info_file.write("\n\n".join([field for field in data if field]))

def _copy_assets(zipdir, assets, asset_filter=[], basename=None):
    if not basename:
        basename = lambda asset: asset.type.name.lower()
    
    for asset in assets:
        if not asset_filter or asset.type in asset_filter:
            path = asset_uploader.path(asset.filename)
            ext = splitext(asset.filename)[-1][1:]
            shutil.copy(path, _filepath(zipdir, basename(asset), ext))

def _filepath(dirpath, basename, ext):
    num = 2
    name = "{name}.{ext}".format(name=basename, ext=ext)
    while exists(join(dirpath, name)):
        name = "{name}_{num}.{ext}".format(name=basename, num=num, ext=ext)
        num += 1
    return join(dirpath, name)