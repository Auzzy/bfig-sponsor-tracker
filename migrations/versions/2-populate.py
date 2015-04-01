"""Populate the DB with users

Revision ID: populate
Revises: init
Create Date: 2015-03-31 01:15:55.339077

"""

import os
import random
import string

from sponsortracker import app, data, model

EMAIL_DELIM = ':'
NAME_DELIM = ','
USERS_DIR = os.path.join(app.config["MIGRATIONS_DIRECTORY"], "configs", "users")

# revision identifiers, used by Alembic.
revision = 'populate'
down_revision = 'init'


'''
def _test_data():
    for role in data.RoleType:
        model.db.session.add(model.Role(type=role.type))
    
    role_dict = {role:model.Role(type=role.type) for role in data.RoleType}
    for user_type in data.UserType:
        email_address = "bfigreceiver@gmail.com" if user_type == data.UserType.ADMIN else "{0}@example.com".format(user_type.type)
        email = model.UserEmail(email=email_address, is_primary=True)
        auth = model.UserAuth(username=user_type.type, password=model.user_manager.hash_password(user_type.type))
        user = model.User(first_name=user_type.type.title(), enabled=True, type=user_type.type, user_auth=auth)
        user.emails.append(email)
        model.db.session.add(user)
'''

def _add_user(type, first_name, last_name, username, email, password=None):
    password = password or ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    email = model.UserEmail(email=email, is_primary=True)
    auth = model.UserAuth(username=username, password=model.user_manager.hash_password(password))
    user = model.User(first_name=first_name, last_name=last_name, enabled=True, type=type, user_auth=auth)
    user.emails.append(email)
    model.db.session.add(user)
    
def _import_users():
    for user_filename in os.listdir(USERS_DIR):
        type = os.path.splitext(user_filename)[0]
        with open(os.path.join(USERS_DIR, user_filename)) as user_file:
            for user_line in user_file:
                name, email = user_line.split(EMAIL_DELIM)
                last_name, first_name = name.split(NAME_DELIM)
                username = email.split('@')[0]
                _add_user(type, first_name, last_name, username, email)

def upgrade():
    # Create roles
    for role in data.RoleType:
        model.db.session.add(model.Role(type=role.type))
    
    # Create admin user
    _add_user(data.UserType.ADMIN.type, "Admin", "Admin", "admin", "austin@bostonfig.com")
    
    _import_users()
    
    model.db.session.commit()


def downgrade():
    model.User.query.delete()
    model.UserAuth.query.delete()
    model.UserEmail.query.delete()
    model.Role.query.delete()
    
    model.db.session.commit()