"""Create roles, add default users

Revision ID: populate
Revises: init
Create Date: 2015-03-31 01:15:55.339077

"""

import random
import string

from sponsortracker import data, model

# revision identifiers, used by Alembic.
revision = 'users'
down_revision = 'init'


def _add_user(type, first_name, last_name, username, email, password=None):
    password = password or ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    email = model.UserEmail(email=email, is_primary=True)
    auth = model.UserAuth(username=username, password=model.user_manager.hash_password(password))
    user = model.User(first_name=first_name, last_name=last_name, enabled=True, type=type, user_auth=auth)
    user.emails.append(email)
    model.db.session.add(user)

def upgrade():
    # Create roles
    for role in data.RoleType:
        model.db.session.add(model.Role(type=role.type))
    
    model.db.session.commit()
    
    # Create admin user
    _add_user(data.UserType.ADMIN.type, "Admin", "Admin", "admin", "austin@bostonfig.com")
    
    model.db.session.commit()


def downgrade():
    model.UserAuth.query.delete()
    model.UserEmail.query.delete()
    model.Role.query.delete()
    model.User.query.delete()
    
    model.db.session.commit()