import flask_wtf
from wtforms import IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Email, Optional

from sponsortracker import data

_SPONSOR_LEVEL_CHOICES = [("", "")] + [(level.name, level.label) for level in data.Level]

class SponsorForm(flask_wtf.Form):
    name = StringField(validators=[DataRequired()])
    email = StringField(validators=[DataRequired(), Email()])
    level_name = SelectField("Level", choices=_SPONSOR_LEVEL_CHOICES, validators=[Optional()])
    cash = IntegerField("Cash Amount (whole USD)", validators=[Optional()])
    inkind = IntegerField("In-kind Amount (whole USD)", validators=[Optional()])