from flask import flash, redirect, render_template, request, url_for
from flask.ext.user import login_required

from sponsortracker import data, forms, model, uploads
from sponsortracker.app import app

@app.route("/sponsor/<int:id>/assets/")
@login_required
def manage_assets(id):
    deal = model.Sponsor.query.get_or_404(id).current
    if deal.level:
        other_assets = set(deal.assets_by_type.keys()) - set(deal.level.assets)
    else:
        other_assets = deal.assets_by_type.keys()
    return render_template("manage-assets.html", deal=deal, other_assets=other_assets)

@app.route("/sponsor/<int:id>/assets/upload/", methods=["GET", "POST"])
@login_required
def upload_asset(id):
    deal = model.Sponsor.query.get_or_404(id).current
    
    asset_types = deal.level.assets if deal.level else list(data.AssetType)
    form = forms.UploadAssetForm(asset_types)
    if form.validate_on_submit():
        return handle_upload(deal, form)
    
    return render_template("upload-asset.html", id=id, form=form, deal=deal)

@app.route("/sponsor/<int:id>/assets/delete/", methods=["POST"])
@login_required
def delete_asset(id):
    asset_id = request.form["asset-id"]
    uploads.Asset.delete(asset_id)
    return redirect(url_for("manage_assets", id=id))

@app.route("/sponsor/<int:id>/assets/preview/", methods=["GET", "POST"])
@login_required
def preview_asset(id):
    filename = request.args.get("filename") or request.values.get("filename")
    type = request.args.get("type") or request.values.get("type")
    
    if not filename or type not in data.AssetType.__members__:
        return redirect(url_for("manage_assets", id=id))
    
    deal = model.Sponsor.query.get_or_404(id).current
    if request.method == "POST":
        if "cancel" in request.form:
            uploads.Preview.discard(deal, filename)
            return redirect(url_for("upload_asset", id=id))
        elif "save" in request.form:
            uploads.Preview.keep(deal, type, filename=filename)
            return redirect(url_for("manage_assets", id=id))
    
    asset_type = data.AssetType[type]
    url = uploads.Preview.url(deal, filename)
    
    # display = uploads.Image(filename, filename=uploads.Preview.path(deal, filename)).format not in [fmt.format for fmt in data._PrintFormat]
    display = True
    return render_template("preview-asset.html", id=id, filename=filename, preview=url, type=asset_type, display=display)

@app.route("/sponsor/<int:id>/assets/increment", methods=["POST"])
@login_required
def increment_asset_usage(id):
    asset_id = request.form["asset-id"]
    model.Asset.query.get_or_404(asset_id).increment_usage()
    model.db.session.commit()
    return redirect(url_for("manage_assets", id=id))

@app.route("/sponsor/<int:id>/assets/decrement", methods=["POST"])
@login_required
def decrement_asset_usage(id):
    asset_id = request.form["asset-id"]
    model.Asset.query.get_or_404(asset_id).decrement_usage()
    model.db.session.commit()
    return redirect(url_for("manage_assets", id=id))

def handle_upload(deal, form):
    preview = uploads.Preview.load(form.asset.data)
    spec = data.AssetType[form.type.data].spec
    
    if data.AssetType[form.type.data] == data.AssetType.LOGO:
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
            # Don't do anything about sizes that don't match. Marketing will handle it.
            pass
        
        if spec.transparent and not preview.alpha_channel:
            preview.alpha_channel = True
        elif spec.transparent is False and preview.alpha_channel:
            preview.alpha_channel = False
    
    if preview.dirty:
        filename = preview.stash(deal)
        return redirect(url_for("preview_asset", id=deal.sponsor.id, filename=filename, type=form.type.data))
    else:
        uploads.Asset.create(deal, form.type.data, form.asset.data)
        return redirect(url_for("manage_assets", id=deal.sponsor.id))