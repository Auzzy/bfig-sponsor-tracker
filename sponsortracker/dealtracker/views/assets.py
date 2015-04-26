from flask import redirect, render_template, request, url_for

from sponsortracker import data, model
from sponsortracker.dealtracker import forms, uploads
from sponsortracker.dealtracker.app import deal_tracker


@deal_tracker.route("/sponsor/<int:id>/assets")
def manage_assets(id):
    return render_template("manage-assets.html", sponsor=model.Sponsor.query.get_or_404(id))

@deal_tracker.route("/sponsor/<int:id>/assets/upload/", methods=["GET", "POST"])
def upload_asset(id):
    sponsor = model.Sponsor.query.get_or_404(id)
    
    form = forms.UploadAssetForm(sponsor.current.level.assets)
    if form.validate_on_submit():
        filename = uploads.verify(id, form)
        if filename:
            return redirect(url_for("dealtracker.preview_asset", id=id, filename=filename, type=form.type.data))
        else:
            return redirect(url_for("dealtracker.manage_assets", id=id))
    
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor)

@deal_tracker.route("/sponsor/<int:id>/assets/delete/", methods=["POST"])
def delete_asset(id):
    asset_id = request.form["asset-id"]
    uploads.Asset.delete(asset_id)
    return redirect(url_for("dealtracker.manage_assets", id=id))

@deal_tracker.route("/sponsor/<int:id>/assets/preview/", methods=["GET", "POST"])
def preview_asset(id):
    filename = request.args.get("filename") or request.values.get("filename")
    type = request.args.get("type") or request.values.get("type")
    
    if not filename or type not in data.AssetType.__members__:
        return redirect(url_for("dealtracker.manage_assets", id=id))
    
    if request.method == "POST":
        if "cancel" in request.form:
            uploads.Preview.discard(id, filename)
            return redirect(url_for("dealtracker.upload_asset", id=id))
        elif "save" in request.form:
            uploads.Preview.stash(id, type, filename)
            return redirect(url_for("dealtracker.manage_assets", id=id))
    
    asset_type = data.AssetType[type]
    url = uploads.Preview.url(id, filename)
    return render_template("preview-asset.html", id=id, filename=filename, preview=url, type=asset_type)
