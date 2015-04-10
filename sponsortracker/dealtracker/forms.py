import datetime
import re

import flask_wtf
from wtforms import HiddenField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Optional

from sponsortracker import data, model

EMAIL_BASENAME = "email"
NAME_BASENAME = "name"

_EMAIL_RE = re.compile("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
_SPONSOR_LEVEL_CHOICES = [("", "")] + [(level.name, level.label) for level in data.Level]
_SPONSOR_TYPE_CHOICES = [("", "")] + [(sponsor_type.name, sponsor_type.value) for sponsor_type in data.SponsorType]

class SponsorForm(flask_wtf.Form):
    name = StringField(validators=[DataRequired()])
    type_name = SelectField("Sponsor Type", choices=_SPONSOR_TYPE_CHOICES, validators=[Optional()])
    notes = TextAreaField(validators=[Optional()])

class CurrentDealForm(flask_wtf.Form):
    owner = SelectField()
    year = HiddenField(default=datetime.date.today().year)
    level_name = SelectField("Level", choices=_SPONSOR_LEVEL_CHOICES, validators=[Optional()])
    cash = IntegerField("Cash Amount (whole USD)", validators=[Optional()])
    inkind = IntegerField("In-kind Amount (whole USD)", validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(CurrentDealForm, self).__init__(*args, **kwargs)
        if "obj" in kwargs:
            self.level_name.data = kwargs["obj"].sponsor.level_name
        
        name_pattern = "{user.last_name}, {user.first_name}"
        sorted_users = sorted(model.User.query.all(), key=lambda user: user.last_name)
        self.owner.choices = [("", "")] + [(user.user_auth.username, name_pattern.format(user=user)) for user in sorted_users if user.type == data.UserType.SALES.type]

def validate_email(email):
    return bool(_EMAIL_RE.match(email))
