from flask import flash

from sponsortracker import model
from sponsortracker.data import AssetType
from sponsortracker.assettracker import data, images, sponsors
from sponsortracker.assettracker.app import asset_uploader

def load_all():
    return [data.Asset.from_model(asset) for asset in model.Asset.query.all()]

def preview(sponsor_id, form):
    preview = images.Preview.load(form.asset.data)
    spec = AssetType[form.type.data].spec
    
    if preview.format not in spec.format_names:
        flash("Image format was {0}. Expected one of the following: {1}.".format(preview.format, ', '.join(spec.format_names)), 'preview')
        format = spec.formats[0] if len(spec.formats) == 1 else type(spec.formats[0]).preferred()
        preview.format = format.format
    
    if preview.colorspace not in spec.color_mode_names:
        flash("Image color mode was {0}. Expected one of the following: {1}.".format(preview.colorspace, ', '.join(spec.color_mode_names)), 'preview')
        preview.colorspace = spec.color_modes[0].value
    
    if preview.resolution != (spec.dpi, spec.dpi):
        flash("Image resolution was {res[0]}x{res[1]}. Expected {spec.dpi}x{spec.dpi}.".format(res=preview.resolution, spec=spec), 'preview')
        preview.resolution = (spec.dpi, spec.dpi)
    
    if preview.width != spec.width or preview.height != spec.height:
        pass
    
    if preview.dirty:
        filename = preview.save(sponsor_id)
        return filename.split('/')[-1]
    return None

def preview_url(sponsor_id, filename):
    return images.Preview.url(sponsor_id, filename)

def save_preview(sponsor_id, type, basename):
    filename = images.Preview.stash(sponsor_id, basename)
    _save(sponsor_id, type, filename)

def discard_preview(sponsor_id, filename):
    images.Preview.discard(sponsor_id, filename)

def save(sponsor_id, form):
    filename = images.Asset.stash(sponsor_id, form.asset.data)
    _save(sponsor_id, form.type.data, filename)

def _save(sponsor_id, type, filename):
    asset_model = data.Asset.new(sponsor_id, type, filename).to_model()
    model.db.session.add(asset_model)
    model.db.session.commit()

def delete(sponsor_id, asset_id):
    asset_model = model.Asset.query.get(asset_id)
    images.Asset.delete(sponsor_id, asset_model.filename)
    
    model.db.session.delete(asset_model)
    model.db.session.commit()