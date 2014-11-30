from sponsortracker import model
from sponsortracker.data import AssetType
from sponsortracker.assettracker import data, images, sponsors
from sponsortracker.assettracker.app import asset_uploader

def preview(sponsor_id, form):
    preview = images.Preview.get(form.asset.data)
    spec = AssetType[form.type.data].spec
    
    if preview.format not in spec.format_names:
        format = spec.formats[0] if len(spec.formats) == 1 else type(spec.formats[0]).preferred()
        preview.format = format.format
    
    if preview.colorspace in spec.color_mode_names:
        preview.colorspace = spec.color_modes[0].value
    
    if preview.resolution != (spec.dpi, spec.dpi):
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