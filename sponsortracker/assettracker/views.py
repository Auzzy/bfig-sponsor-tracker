from flask import redirect, render_template, request, url_for

from sponsortracker.assettracker import assets, data, forms, sponsors
from sponsortracker.assettracker.app import asset_tracker

@asset_tracker.route("/")
def home():
    sponsors_by_level = sponsors.load_all_by_level()
    return render_template("assettracker.html", sponsors_by_level=sponsors_by_level)

@asset_tracker.route("/sponsor/<int:id>/", methods=["GET", "POST"])
def sponsor_page(id):
    info_forms = sponsors.load_info(id)
    for form in info_forms:
        if form.__class__.__name__ == form.form_type.data and form.validate_on_submit():
            sponsors.save_info(id, form)
            return redirect(url_for("assettracker.sponsor_page", id=id))
    sponsor = sponsors.load(id)
    return render_template("sponsor-page.html", sponsor=sponsor, info_forms=info_forms)

@asset_tracker.route("/sponsor/<int:id>/upload-asset/", methods=["GET", "POST"])
def upload_asset(id):
    form = forms.UploadAssetForm()
    if form.validate_on_submit():
        filename = assets.preview(id, form)
        if filename:
            return redirect(url_for("assettracker.preview_asset", id=id, filename=filename))
        else:
            return redirect(url_for("assettracker.sponsor_page", id=id))
    
    sponsor = sponsors.load(id)
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor, assets=sponsor.assets)

@asset_tracker.route("/sponsor/<int:id>/preview-asset/<filename>")
def preview_asset(id, filename):
    form = forms.PreviewAssetForm()
    if form.validate_on_submit():
        pass
    
    orig_url,preview_url = assets.preview_urls(id, filename)
    return render_template("preview-asset.html", id=id, original=orig_url, preview=preview_url)

@asset_tracker.route("/sponsor/<int:id>/view-assets/")
def view_assets(id):
    sponsor = sponsors.load(id)
    return render_template("view-assets.html", sponsor=sponsor)

