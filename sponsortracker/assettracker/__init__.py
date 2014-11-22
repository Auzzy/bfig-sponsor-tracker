from flask import Blueprint
from flaskext.uploads import configure_uploads, UploadSet

from sponsortracker.assettracker.app import asset_uploader, preview_uploader, thumb_uploader
from sponsortracker.app import app

configure_uploads(app, (asset_uploader, preview_uploader, thumb_uploader))

from . import views