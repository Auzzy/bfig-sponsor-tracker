from flask import Blueprint
from flaskext.uploads import UploadSet

from sponsortracker import data

deal_tracker = Blueprint('dealtracker', __name__, template_folder='templates', static_folder='static')

preview_uploader = UploadSet("previews", data.ASSET_FORMATS_EXT)