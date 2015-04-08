import os
import random
import string

from sponsortracker import data, model

EMAIL_DELIM = ':'
NAME_DELIM = ','
USERS_DIR = "users/"

def _add_user(type, first_name, last_name, username, email, password=None):
    if model.UserAuth.query.filter_by(username=username).all():
        return
    
    password = password or ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    
    email = model.UserEmail(email=email, is_primary=True)
    auth = model.UserAuth(username=username, password=model.user_manager.hash_password(password))
    user = model.User(first_name=first_name, last_name=last_name, enabled=True, type=type, user_auth=auth)
    user.emails.append(email)
    model.db.session.add(user)
    
    print("Added {0} {1} ({2})".format(first_name, last_name, username))
    
def _import_users():
    for user_filename in os.listdir(USERS_DIR):
        type = os.path.splitext(user_filename)[0]
        with open(os.path.join(USERS_DIR, user_filename)) as user_file:
            for user_line in user_file.readlines():
                name, email = user_line.split(EMAIL_DELIM)
                last_name, first_name = name.split(NAME_DELIM)
                username = email.split('@')[0]
                _add_user(type, first_name, last_name, username, email)

def main():
    _import_users()
    
    model.db.session.commit()

if __name__ == "__main__":
    main()