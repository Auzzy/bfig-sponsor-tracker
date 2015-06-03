from flask import redirect, render_template, request, url_for
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
        filename = uploads.verify(deal, form)
        if filename:
            return redirect(url_for("preview_asset", id=id, filename=filename, type=form.type.data))
        else:
            return redirect(url_for("manage_assets", id=id))
    
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
