import os
import random
import string

from sponsortracker import data, model

EMAIL_DELIM = ':'
NAME_DELIM = ','
PLACEHOLDER_USERS_FILENAME = "placeholder.txt"
USER_FILE_MAP = {
    data.UserType.ADMIN.type: "admin.txt",
    data.UserType.SALES.type: "sales.txt"
}
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
    for user_type in USER_FILE_MAP:
        with open(os.path.join(USERS_DIR, USER_FILE_MAP[user_type])) as user_file:
            for user_line in user_file:
                user_line = user_line.strip()
                name, email = user_line.split(EMAIL_DELIM)
                last_name, first_name = name.split(NAME_DELIM)
                username = email.split('@')[0]
                _add_user(user_type, first_name, last_name, username, email)
    
    '''
    with open(os.path.join(USERS_DIR, PLACEHOLDER_USERS_FILENAME)) as user_file:
        for name in user_file:
            name = name.strip()
            username = "{0}-pseudoacct".format(name.lower())
            if not model.PseudoUser.query.filter_by(username=username).first():
                model.db.session.add(model.PseudoUser(first_name=name, username=username))
                print("Added pseudouser {0} ({1})".format(name, username))
    '''
    
def main():
    _import_users()
    
    model.db.session.commit()

if __name__ == "__main__":
    main()