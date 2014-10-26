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
    if request.method == "POST":
        if form.validate_on_submit():
            assets.save(id, form)
    
    sponsor = sponsors.load(id)
    return render_template("upload-asset.html", id=id, form=form, sponsor=sponsor, assets=sponsor.assets)

@asset_tracker.route("/view-assets/<int:id>/")
def view_assets(id):
    sponsor = sponsors.load(id)
    return render_template("view-assets.html", sponsor=sponsor)