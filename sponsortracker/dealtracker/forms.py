import datetime
import re

import flask_wtf
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import HiddenField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional, URL, ValidationError

from sponsortracker import data, model
from sponsortracker.dealtracker.app import asset_uploader
from sponsortracker.dealtracker import uploads

EMAIL_BASENAME = "email"
NAME_BASENAME = "name"

_EMAIL_RE = re.compile("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
_SPONSOR_LEVEL_CHOICES = [("", "")] + [(level.name, level.label) for level in data.Level]
_SPONSOR_TYPE_CHOICES = [("", "")] + [(sponsor_type.name, sponsor_type.value) for sponsor_type in data.SponsorType]

def validate_email(email):
    return bool(_EMAIL_RE.match(email))

def validate_asset(form, field):
    image = uploads.Image.load(field.data)
    spec = data.AssetType[form.type.data].spec
    
    if spec.transparent and not image.alpha_channel:
        raise ValidationError("Expected a transparent background.")
    elif spec.transparent is False and image.alpha_channel:
        raise ValidationError("Expected an opaque background.")

def validate_sponsor(form, field):
    if model.Sponsor.query.filter_by(name=field.data):
        raise ValidationError("A sponsor with that name already exists.")

class SponsorForm(flask_wtf.Form):
    name = StringField(validators=[DataRequired(), validate_sponsor])
    type_name = SelectField("Sponsor Type", choices=_SPONSOR_TYPE_CHOICES, validators=[Optional()])
    link = StringField("Home page", validators=[URL(), Optional()])
    description = TextAreaField(validators=[Optional()])
    notes = TextAreaField(validators=[Optional()])

class CurrentDealForm(flask_wtf.Form):
    owner = SelectField()
    year = HiddenField(default=datetime.date.today().year)
    level_name = SelectField("Level", choices=_SPONSOR_LEVEL_CHOICES, validators=[Optional()])
    cash = IntegerField("Cash Amount (whole USD)", validators=[Optional()])
    inkind = IntegerField("In-kind Amount (whole USD)", validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(CurrentDealForm, self).__init__(*args, **kwargs)
        
        name_pattern = "{user.last_name}, {user.first_name}"
        sorted_users = sorted(model.User.query.all(), key=lambda user: user.last_name)
        self.owner.choices = [("", "")] + [(user.user_auth.username, name_pattern.format(user=user)) for user in sorted_users if user.type == data.UserType.SALES]

class UploadAssetForm(flask_wtf.Form):
    type = SelectField(validators=[DataRequired("You must select an asset type.")])
    asset = FileField(validators=[FileRequired(), FileAllowed(asset_uploader, "The uploaded asset must be an image file."), validate_asset])
    
    def __init__(self, asset_types=[], *args, **kwargs):
        super(UploadAssetForm, self).__init__(*args, **kwargs)
        
        asset_types = asset_types or list(data.AssetType)
        self.type.choices = [(type.name, type.label) for type in sorted(asset_types, key=lambda type: type.label)]