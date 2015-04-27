from flask import redirect, render_template, request, url_for

from sponsortracker import data, model
from sponsortracker.dealtracker import forms, uploads
from sponsortracker.dealtracker.app import deal_tracker


@deal_tracker.route("/sponsor/<int:id>/assets")
def manage_assets(id):
    return render_template("manage-assets.html", deal=model.Sponsor.query.get_or_404(id).current)

@deal_tracker.route("/sponsor/<int:id>/assets/upload/", methods=["GET", "POST"])
def upload_asset(id):
    deal = model.Sponsor.query.get_or_404(id).current
    
    form = forms.UploadAssetForm(deal.level.assets)
    if form.validate_on_submit():
        filename = uploads.verify(deal, form)
        if filename:
            return redirect(url_for("dealtracker.preview_asset", id=id, filename=filename, type=form.type.data))
        else:
            return redirect(url_for("dealtracker.manage_assets", id=id))
    
    return render_template("upload-asset.html", id=id, form=form, deal=deal)

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
    
    deal = model.Sponsor.query.get_or_404(id).current
    if request.method == "POST":
        if "cancel" in request.form:
            uploads.Preview.discard(deal, filename)
            return redirect(url_for("dealtracker.upload_asset", id=id))
        elif "save" in request.form:
            uploads.Preview.stash(deal, type, filename)
            return redirect(url_for("dealtracker.manage_assets", id=id))
    
    asset_type = data.AssetType[type]
    url = uploads.Preview.url(deal, filename)
    return render_template("preview-asset.html", id=id, filename=filename, preview=url, type=asset_type)