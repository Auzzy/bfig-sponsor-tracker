from flask import flash, get_flashed_messages, redirect, render_template, request, send_file, url_for
from flask.ext.login import current_user

import datetime

from sponsortracker.data import AssetType
from sponsortracker.model import Asset, Sponsor
from sponsortracker.assettracker import asset_request, download, forms, uploads
from sponsortracker.assettracker.app import asset_tracker

UPDATE_DATE_FORMAT = "%a %b %d %Y"

@asset_tracker.route("/")
def home():
    assets = Asset.query.all()
    min_asset_date = min(assets, key=lambda asset: asset.date).date if assets else datetime.date.today()
    sponsors = Sponsor.query.filter(Sponsor.level_name != None).filter(Sponsor.level_name != '')
    return render_template("assettracker.html", sponsors=sponsors, min_asset_date=min_asset_date)

@asset_tracker.route("/download/all/")
def download_all():
    zipfilename = download.all()
    return send_file(zipfilename, as_attachment=True)

@asset_tracker.route("/download/logo_cloud/")
def download_logo_cloud():
    zipfilename = download.logo_cloud()
    return send_file(zipfilename, as_attachment=True)

@asset_tracker.route("/download/website_updates/")
def download_website_updates():
    date = datetime.datetime.strptime(request.args["website-updates-date"], UPDATE_DATE_FORMAT).date()
    zipfilename = download.website_updates(date)
    return send_file(zipfilename, as_attachment=True)


@asset_tracker.route("/sponsor/<int:id>/")
def sponsor_page(id):
    sponsor = Sponsor.query.get_or_404(id)
    errors = get_flashed_messages(category_filter=["error"])
    info_forms = {
        "link":forms.LinkForm(info=sponsor.link),
        "description":forms.DescriptionForm(info=sponsor.description)
    }
    return render_template("sponsor-page.html", sponsor=sponsor, forms=info_forms, errors=errors)

@asset_tracker.route("/sponsor/<int:id>/link/", methods=["POST"])
def info_link(id):
    form = forms.LinkForm()
    if form.validate_on_submit():
        Sponsor.query.get_or_404(id).save_link(form)
    else:
        flash("Invalid link", "error")
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/description/", methods=["POST"])
def info_description(id):
    form = forms.DescriptionForm()
    if form.validate_on_submit():
        Sponsor.query.get_or_404(id).save_description(form)
    else:
        flash("Invalid description", "error")
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/asset-request/", methods=["POST"])
def send_asset_request(id):
    asset_request.send(Sponsor.query.get_or_404(id))
    
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/upload-asset/", methods=["GET", "POST"])
def upload_asset(id):
    sponsor = Sponsor.query.get_or_404(id)
    
    form = forms.UploadAssetForm(sponsor.level.assets)
    if form.validate_on_submit():
        filename = uploads.verify(id, form)
        if filename:
            return redirect(url_for("assettracker.preview_asset", id=id, filename=filename, type=form.type.data))
        else:
            return redirect(url_for("assettracker.sponsor_page", id=id))
    
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor, assets=sponsor.assets)

@asset_tracker.route("/sponsor/<int:id>/delete-asset/", methods=["POST"])
def delete_asset(id):
    asset_id = request.form["asset-id"]
    uploads.Asset.delete(asset_id)
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/preview-asset/", methods=["GET", "POST"])
def preview_asset(id):
    filename = request.args.get("filename") or request.values.get("filename")
    type = request.args.get("type") or request.values.get("type")
    
    if not filename or type not in AssetType.__members__:
        return redirect(url_for("assettracker.sponsor_page", id=id))
    
    if request.method == "POST":
        if "cancel" in request.form:
            uploads.Preview.discard(id, filename)
            return redirect(url_for("assettracker.upload_asset", id=id))
        elif "save" in request.form:
            uploads.Preview.stash(id, type, filename)
            return redirect(url_for("assettracker.sponsor_page", id=id))
    
    asset_type = AssetType[type]
    url = uploads.Preview.url(id, filename)
    return render_template("preview-asset.html", id=id, filename=filename, preview=url, type=asset_type)
