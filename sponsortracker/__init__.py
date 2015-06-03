from flask.ext.user import SQLAlchemyAdapter, UserManager
from flaskext.uploads import configure_uploads, UploadSet

from sponsortracker import model
from sponsortracker.app import app, preview_uploader

# Patch Flask Uploads lack of spport for Python 3
class PatchedDict(dict):
    def itervalues(self):
        return self.values()
app.upload_set_config = PatchedDict()

configure_uploads(app, (preview_uploader))

from . import views