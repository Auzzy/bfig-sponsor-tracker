from flask import Blueprint
from flaskext.uploads import UploadSet

from sponsortracker import data

asset_tracker = Blueprint('assettracker', __name__, template_folder='templates', static_folder='static')
asset_uploader = UploadSet('assets', data.ASSET_FORMATS_EXT)