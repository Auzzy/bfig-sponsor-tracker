from flask import flash, get_flashed_messages, redirect, render_template, request, send_file, url_for
from flask.ext.login import current_user
from flask.ext.user import roles_required

from sponsortracker.data import AssetType, RoleType
from sponsortracker.assettracker import assets, data, download, forms, sponsors
from sponsortracker.assettracker.app import asset_tracker

@asset_tracker.route("/")
@roles_required([RoleType.AT_READ, RoleType.AT_WRITE])
def home():
    min_asset_date = min(assets.load_all(), key=lambda asset: asset.date).date
    return render_template("assettracker.html", sponsors=sponsors.load_all(), min_asset_date=min_asset_date)

@asset_tracker.route("/download/all")
@roles_required([RoleType.AT_READ])
def download_all():
    zipfilename = download.all()
    return send_file(zipfilename, as_attachment=True)

@asset_tracker.route("/download/logo_cloud")
@roles_required([RoleType.AT_READ])
def download_logo_cloud():
    zipfilename = download.logo_cloud()
    return send_file(zipfilename, as_attachment=True)

@asset_tracker.route("/download/website_updates")
@roles_required([RoleType.AT_READ])
def download_website_updates():
    print(request.args["date"])
    return redirect(url_for("assettracker.home"))

@asset_tracker.route("/sponsor/<int:id>/")
@roles_required([RoleType.AT_READ, RoleType.AT_WRITE])
def sponsor_page(id):
    readonly = not current_user.has_roles(RoleType.AT_WRITE)
    sponsor = sponsors.load(id)
    sponsor_info = sponsors.load_info(id)
    forms = {} if readonly else {info:info.form_cls(info=sponsor_info[info]) for info in data.InfoData}
    errors = get_flashed_messages(category_filter=["error"])
    return render_template("sponsor-page.html", sponsor=sponsor, forms=forms, readonly=readonly, errors=errors)

@asset_tracker.route("/sponsor/<int:id>/link/", methods=["POST"])
@roles_required([RoleType.AT_WRITE])
def info_link(id):
    form = forms.LinkForm()
    if form.validate_on_submit():
        sponsors.save_link(id, form)
    else:
        flash("Invalid link", "error")
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/description/", methods=["POST"])
@roles_required([RoleType.AT_WRITE])
def info_description(id):
    form = forms.DescriptionForm()
    if form.validate_on_submit():
        sponsors.save_description(id, form)
    else:
        flash("Invalid description", "error")
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/upload-asset/", methods=["GET", "POST"])
@roles_required([RoleType.AT_WRITE])
def upload_asset(id):
    sponsor = sponsors.load(id)
    
    form = forms.UploadAssetForm(sponsor.level.assets)
    if form.validate_on_submit():
        filename = assets.preview(id, form)
        if filename:
            return redirect(url_for("assettracker.preview_asset", id=id, filename=filename, type=form.type.data))
        else:
            return redirect(url_for("assettracker.sponsor_page", id=id))
    
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor, assets=sponsor.assets)

@asset_tracker.route("/sponsor/<int:id>/delete-asset", methods=["POST"])
@roles_required([RoleType.AT_WRITE])
def delete_asset(id):
    asset_id = request.form["asset-id"]
    assets.delete(id, asset_id)
    return redirect(url_for("assettracker.sponsor_page", id=id))

@asset_tracker.route("/sponsor/<int:id>/preview-asset/", methods=["GET", "POST"])
@roles_required([RoleType.AT_WRITE])
def preview_asset(id):
    filename = request.args.get("filename") or request.values.get("filename")
    type = request.args.get("type") or request.values.get("type")
    
    if not filename or type not in AssetType.__members__:
        return redirect(url_for("assettracker.sponsor_page", id=id))
    
    if request.method == "POST":
        if "cancel" in request.form:
            assets.discard_preview(id, filename)
            return redirect(url_for("assettracker.upload_asset", id=id))
        elif "save" in request.form:
            assets.save_preview(id, type, filename)
            return redirect(url_for("assettracker.sponsor_page", id=id))
    
    asset_type = AssetType[type]
    url = assets.preview_url(id, filename)
    return render_template("preview-asset.html", id=id, filename=filename, preview=url, type=asset_type)
