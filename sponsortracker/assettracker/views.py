from flask import redirect, render_template, request, url_for

from sponsortracker.assettracker import assets, data, forms, sponsors
from sponsortracker.assettracker.app import asset_tracker

@asset_tracker.route("/")
def home():
    sponsors_by_level = sponsors.load_all_by_level()
    return render_template("assettracker.html", sponsors_by_level=sponsors_by_level)

@asset_tracker.route("/upload-asset/<int:id>/", methods=["GET", "POST"])
def upload_asset(id):
    form = forms.UploadAssetForm()
    if form.validate_on_submit():
        assets.save(id, form)
        return redirect(url_for("assettracker.sponsor_page", id=id))
    
    sponsor = sponsors.load(id)
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor, assets=sponsor.assets)

@asset_tracker.route("/view-assets/<int:id>/")
def view_assets(id):
    sponsor = sponsors.load(id)
    return render_template("view-assets.html", sponsor=sponsor)

@asset_tracker.route("/sponsor/<int:id>/", methods=["GET", "POST"])
def sponsor_page(id):
    info_forms = sponsors.load_info(id)
    for form in info_forms:
        if form.__class__.__name__ == form.form_type.data and form.validate_on_submit():
            sponsors.save_info(id, form)
            return redirect(url_for("assettracker.sponsor_page", id=id))
    sponsor = sponsors.load(id)
    return render_template("sponsor_page.html", sponsor=sponsor, info_forms=info_forms)
