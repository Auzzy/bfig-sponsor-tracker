import flask_wtf
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired, Optional, URL

from sponsortracker import data
from sponsortracker.assettracker.app import asset_uploader

_ASSET_CHOICES = [(type.name, type.label) for type in sorted(data.AssetType, key=lambda type: type.label)]

class UploadAssetForm(flask_wtf.Form):
    type = SelectField(choices=_ASSET_CHOICES, validators=[InputRequired("You must select an asset type.")])
    asset = FileField(validators=[FileRequired(), FileAllowed(asset_uploader, "The uploaded asset must be an image file.")])
    
class LinkForm(flask_wtf.Form):
    form_type = HiddenField(default="LinkForm")
    link = StringField("Home page", validators=[URL(), Optional()])

class DescriptionForm(flask_wtf.Form):
    form_type = HiddenField(default="DescriptionForm")
    description = TextAreaField(validators=[Optional()])