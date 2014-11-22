from os.path import join, splitext

from sponsortracker import model
from sponsortracker.data import AssetType
from sponsortracker.assettracker import data, sponsors
from sponsortracker.assettracker.app import asset_uploader, preview_uploader

def save(sponsor_id, form):
    asset_model = data.Asset.from_form(form, sponsor_id).to_model()
    model.db.session.add(asset_model)
    model.db.session.commit()

def preview(sponsor_id, form):
    image = data.load_image(form.asset)
    spec = AssetType[form.type.data].spec
    
    preview_image = image.clone()
    if image.format not in spec.format_names:
        format = spec.formats[0] if len(spec.formats) == 1 else type(spec.formats[0]).preferred()
        preview_image.format = format.format
    
    if image.colorspace in spec.color_mode_names:
        preview_image.colorspace = spec.color_modes[0].value
    
    if image.resolution != (spec.dpi, spec.dpi):
        preview_image.resolution = (spec.dpi, spec.dpi)
    
    if image.width != spec.width or image.height != spec.height:
        pass
    
    if preview_image.dirty:
        filename = form.asset.data.filename
        orig_filename,preview_filename = _image_filenames(filename)
        
        print("ORIG FILENAME: " + str(orig_filename))
        print("PREVIEW FILENAME: " + str(preview_filename))
        
        data.save_image(image, preview_uploader, folder=str(sponsor_id), name=orig_filename)
        data.save_image(preview_image, preview_uploader, folder=str(sponsor_id), name=preview_filename)
        return filename
    return None

def preview_urls(sponsor_id, filename):
    orig_filename,preview_filename = _image_filenames(filename)
    return preview_uploader.url(join(str(sponsor_id), orig_filename)), preview_uploader.url(join(str(sponsor_id), preview_filename))

def _image_filenames(filename):
    return _image_filename(filename, "orig"), _image_filename(filename, "preview")

def _image_filename(filename, tag):
    root, ext = splitext(filename)
    return "{root}_{tag}{ext}".format(root=root, tag=tag, ext=ext)
