import datetime

from flask import request, send_file
from flask.ext.user import login_required

from sponsortracker import data, download
from sponsortracker.app import app

UPDATE_DATE_FORMAT = "%a %b %d %Y"

@app.route("/download/all/")
@app.route("/download/all/<level>/")
@login_required
def download_all(level=None):
    zipfilename = download.all(level)
    return send_file(zipfilename, as_attachment=True)

@app.route("/download/logo_cloud/")
@app.route("/download/logo_cloud/<level>/")
@login_required
def download_logo_cloud(level=None):
    zipfilename = download.logo_cloud(level)
    return send_file(zipfilename, as_attachment=True)

@app.route("/download/website_updates/")
@app.route("/download/website_updates/<level>")
@login_required
def download_website_updates(level=None):
    date = datetime.datetime.strptime(request.args["date"], UPDATE_DATE_FORMAT).date()
    zipfilename = download.website_updates(date, level)
    return send_file(zipfilename, as_attachment=True)
