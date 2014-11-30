import flask_wtf
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired, Optional, URL, ValidationError

from sponsortracker.data import AssetType
from sponsortracker.assettracker.images import Image
from sponsortracker.assettracker.app import asset_uploader

_ASSET_CHOICES = [(type.name, type.label) for type in sorted(AssetType, key=lambda type: type.label)]

def validate_asset(form, field):
    image = Image.load(field.data)
    spec = AssetType[form.type.data].spec
    
    if spec.transparent and not image.alpha_channel:
        raise ValidationError("Expected a transparent background.")
    elif spec.transparent is False and image.alpha_channel:
        raise ValidationError("Expected an opaque background.")
    
    if image.width != spec.width or image.height != spec.height:
        # raise ValidationError("Expected image size to be {0}x{1}, but provided image was {2}x{3}".format(image.width, image.height, spec.width, spec.height)
        pass

class UploadAssetForm(flask_wtf.Form):
    type = SelectField(choices=_ASSET_CHOICES, validators=[InputRequired("You must select an asset type.")])
    asset = FileField(validators=[FileRequired(), FileAllowed(asset_uploader, "The uploaded asset must be an image file."), validate_asset])
    
class LinkForm(flask_wtf.Form):
    form_type = HiddenField(default="LinkForm")
    link = StringField("Home page", validators=[URL(), Optional()])

class DescriptionForm(flask_wtf.Form):
    form_type = HiddenField(default="DescriptionForm")
    description = TextAreaField(validators=[Optional()])