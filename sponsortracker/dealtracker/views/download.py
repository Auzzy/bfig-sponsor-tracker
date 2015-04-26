'''
import datetime

from flask import request, send_file

from sponsortracker import data, model
from sponsortracker.dealtracker import download
from sponsortracker.dealtracker.app import deal_tracker

UPDATE_DATE_FORMAT = "%a %b %d %Y"


@deal_tracker.route("/download/all/")
def download_all():
    zipfilename = download.all()
    return send_file(zipfilename, as_attachment=True)

@deal_tracker.route("/download/logo_cloud/")
def download_logo_cloud():
    zipfilename = download.logo_cloud()
    return send_file(zipfilename, as_attachment=True)

@deal_tracker.route("/download/website_updates/")
def download_website_updates():
    date = datetime.datetime.strptime(request.args["website-updates-date"], UPDATE_DATE_FORMAT).date()
    zipfilename = download.website_updates(date)
    return send_file(zipfilename, as_attachment=True)
'''