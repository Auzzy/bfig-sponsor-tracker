from enum import Enum

from flask.ext.user import SQLAlchemyAdapter, UserManager, UserMixin

from sponsortracker.model import db

_DB_ADAPTER = None
_USER_MANAGER = None

class RoleTypes(Enum):
    ADMIN = "admin"
    EXEC = "exec"
    SALES = "sales"
    MARKETING = "marketing"
    COORD = "coord"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, default='')
    last_name = db.Column(db.String(50), nullable=False, default='')
    enabled = db.Column(db.Boolean(), nullable=False, default=False)
    emails = db.relationship('UserEmail')
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    user_auth = db.relationship('UserAuth', uselist=False)

    def is_active(self):
      return self.enabled

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
    name = db.Column(db.String(50), unique=True)
    
class UserRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

def init(app):
    global _DB_ADAPTER, _USER_MANAGER
    _DB_ADAPTER = _DB_ADAPTER or SQLAlchemyAdapter(db, User, UserAuthClass=UserAuth, UserEmailClass=UserEmail)
    _USER_MANAGER = _USER_MANAGER or UserManager(_DB_ADAPTER, app)
    
    return _DB_ADAPTER, _USER_MANAGER

# This should be moved into a migration file
def _init_data():
    for role_type in RoleTypes:
        role = Role(name=role_type.value)
        email_address = "bfigreceiver@gmail.com" if role_type == RoleTypes.ADMIN else "{0}@example.com".format(role_type.value)
        email = UserEmail(email=email_address, is_primary=True)
        auth = UserAuth(username=role_type.value, password=_USER_MANAGER.hash_password(role_type.value))
        user = User(first_name=role_type.value.title(), enabled=True, user_auth=auth)
        user.roles.append(role)
        user.emails.append(email)
        db.session.add(user)
    
    db.session.commit()