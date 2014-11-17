import flask_wtf
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import HiddenField, SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired, Optional, URL, ValidationError

from wand.image import Image
from PIL import Image as PillowImage

from sponsortracker import data
from sponsortracker.assettracker.app import asset_uploader

_ASSET_CHOICES = [(type.name, type.label) for type in sorted(data.AssetType, key=lambda type: type.label)]


def validate_asset(form, field):
    image = Image(file=field.data.stream)
    spec = data.AssetType[form.type.data].spec
    
    print("SIZE: " + str(image.size))
    print("FORMAT: " + str(image.format))
    print("COLORSPACE: " + str(image.colorspace))
    print("RESOLUTION: " + str(image.resolution))
    print("ALPHA: " + str(image.alpha_channel))
    
    if image.format not in spec.formats:
        raise ValidationError("Unexpected file format. Expected: {0}, but is {1}.".format(spec.formats_as_str(), image.format))
    if image.colorspace in spec.color_modes:
        raise ValidationError("Unexpected color mode. Expected: {0}, but is {1}".format(spec.color_modes_as_str(), image.colorspace))
    if image.resolution == (spec.dpi, spec.dpi):
        raise ValidationError("Expected image resolution to be {0} dpi, but is {1} dpi.")
    
    if spec.transparent and not image.alpha_channel:
        raise ValidationError("Expected a transparent background.")
    elif spec.transparent is False and image.alpha_channel:
        raise ValidationError("Expected an opaque background.")
    
    if image.width == spec.width and image.height == spec.height:
        pass
    
    raise ValidationError("Validation succeeded")


class UploadAssetForm(flask_wtf.Form):
    type = SelectField(choices=_ASSET_CHOICES, validators=[InputRequired("You must select an asset type.")])
    asset = FileField(validators=[FileRequired(), FileAllowed(asset_uploader, "The uploaded asset must be an image file."), validate_asset])
    
class LinkForm(flask_wtf.Form):
    form_type = HiddenField(default="LinkForm")
    link = StringField("Home page", validators=[URL(), Optional()])

class DescriptionForm(flask_wtf.Form):
    form_type = HiddenField(default="DescriptionForm")
    description = TextAreaField(validators=[Optional()])