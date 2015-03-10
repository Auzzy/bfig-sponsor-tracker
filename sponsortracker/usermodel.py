from enum import Enum

from flask.ext.user import SQLAlchemyAdapter, UserManager, UserMixin
from wtforms.validators import ValidationError
from sqlalchemy import event

from sponsortracker import data
from sponsortracker.model import db

_DB_ADAPTER = None
_USER_MANAGER = None

_USER_TYPES = [user_type.type for user_type in data.UserType]

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    type = db.Column(db.Enum(name="UserType", *_USER_TYPES), nullable=False)
    emails = db.relationship('UserEmail')
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    user_auth = db.relationship('UserAuth', uselist=False)
    
    def is_active(self):
        return self.enabled
    
    def has_roles(self, *roles):
        return super(User, self).has_roles(*data.RoleType.types(roles))

@event.listens_for(User.type, 'set')
def handle_type_change(user, type, old_type, initiator):
    if type != old_type:
        roles = data.UserType.from_type(type).roles
        role_types = data.RoleType.types(roles)
        user.roles = Role.query.filter(Role.type.in_(role_types)).all()

class UserEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    email = db.Column(db.String(255), nullable=False, unique=True)
    is_primary = db.Column(db.Boolean(), nullable=False, default=False)
    confirmed_at = db.Column(db.DateTime())
    user = db.relationship('User', uselist=False)

class UserAuth(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, default='')
    reset_password_token = db.Column(db.String(100), nullable=False, default='')
    user = db.relationship('User', uselist=False, foreign_keys=user_id)

class Role(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    type = db.Column(db.String(50), unique=True)
    
    def __getattr__(self, name):
        if name == "name":
            return self.type
        return super(Role, self).__getattr__(self, name)
    
class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("role.id", ondelete="CASCADE"))

def init(app):
    global _DB_ADAPTER, _USER_MANAGER
    _DB_ADAPTER = _DB_ADAPTER or SQLAlchemyAdapter(db, User, UserAuthClass=UserAuth, UserEmailClass=UserEmail)
    _USER_MANAGER = _USER_MANAGER or UserManager(_DB_ADAPTER, app, password_validator=password_validator)
    
    return _DB_ADAPTER, _USER_MANAGER

def password_validator(form, field):
    password = field.data
    if len(password) < 6:
        raise ValidationError("Password must have at least 6 characters.")

# TODO: Move into a migration file
def _init_data():
    for role in data.RoleType:
        db.session.add(Role(type=role.type))
    
    role_dict = {role:Role(type=role.type) for role in data.RoleType}
    for user_type in data.UserType:
        email_address = "bfigreceiver@gmail.com" if user_type == data.UserType.ADMIN else "{0}@example.com".format(user_type.type)
        email = UserEmail(email=email_address, is_primary=True)
        auth = UserAuth(username=user_type.type, password=_USER_MANAGER.hash_password(user_type.type))
        user = User(first_name=user_type.type.title(), enabled=True, type=user_type.type, user_auth=auth)
        user.emails.append(email)
        db.session.add(user)
    
    db.session.commit()