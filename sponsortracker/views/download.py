import datetime

from flask import request, send_file
from flask.ext.user import login_required

from sponsortracker import data, download
from sponsortracker.app import app

UPDATE_DATE_FORMAT = "%a %b %d %Y"

@app.route("/download/all/")
@login_required
def download_all():
    zipfilename = download.all()
    return send_file(zipfilename, as_attachment=True)

@app.route("/download/logo_cloud/")
@login_required
def download_logo_cloud():
    zipfilename = download.logo_cloud()
    return send_file(zipfilename, as_attachment=True)

@app.route("/download/website_updates/")
@login_required
def download_website_updates():
    date = datetime.datetime.strptime(request.args["website-updates-date"], UPDATE_DATE_FORMAT).date()
    zipfilename = download.website_updates(date)
    return send_file(zipfilename, as_attachment=True)
