import collections
import datetime
import itertools
import random
import string
from collections import OrderedDict

from flask import redirect, render_template, request, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sqlalchemy import or_

from sponsortracker import forms, model
from sponsortracker.app import app
from sponsortracker.data import AssetType, Level, UserType


DATE_FORMAT = "%a %b %d %Y"
REQUEST_ID = "request-date"

@app.route("/")
@login_required
def home():
    if current_user.type == UserType.SALES.type:
        return sales_home()
    elif current_user.type == UserType.MARKETING.type:
        return marketing_home()
    
    return redirect(url_for("all_deals"))

def sales_home():
    year = datetime.datetime.today().year
    deals = model.Deal.query.filter_by(owner=current_user.user_auth.username, year=year)
    sponsors = [deal.sponsor for deal in deals]
    return render_template("sponsor-list.html", sponsors=sponsors, year=year)

@app.route("/assets/")
@login_required
def marketing_home():
    current_query = model.Deal.query.filter_by(year=datetime.date.today().year)
    deals_by_level = collections.OrderedDict()
    for level in Level:
        ready = lambda deal: bool(deal.contract.received != None or deal.invoice.received != None) if level == Level.INDIE else lambda deal: bool(deal.asset_request.sent != None)
        deals_by_level[level] = [deal for deal in current_query.filter_by(level_name=level.name) if ready(deal)]
    return render_template("marketing-home.html", deals_by_level=deals_by_level)
    
@app.route("/all/")
@login_required
def all_deals():
    return render_template("sponsor-list.html", sponsors=model.Sponsor.query)

@app.route("/users/manage/")
@login_required
def manage_users():
    return render_template("manage-users.html", users=model.User.query.filter(model.User.type_name != UserType.ADMIN.name))

@app.route("/users/edit/", methods=["GET", "POST"])
@app.route("/users/edit/<int:id>/", methods=["GET", "POST"])
@login_required
def configure_user(id=None):
    if request.method == "POST":
        form = forms.UserForm()
        if form.validate_on_submit():
            username = form.username.data or form.email.data.split('@')[0]
            _configure_user(id, form.type_name.data, form.first_name.data, form.last_name.data, form.email.data, username)
            return redirect(url_for("manage_users"))
    else:
        form = forms.UserForm(obj=model.User.query.get_or_404(id)) if id else forms.UserForm()
    return render_template("configure-user.html", id=id, form=form)

@app.route("/users/delete/", methods=["POST"])
@login_required
def delete_user():
    id = request.form["user-id"]
    model.db.session.delete(model.User.query.get_or_404(id))
    model.db.session.commit()
    return redirect(url_for("manage_users"))

@app.route("/sponsor/<int:id>/")
@login_required
def sponsor_info(id):
    sponsor = model.Sponsor.query.get_or_404(id)
    return render_template("sponsor-info.html", sponsor=sponsor, request_id=REQUEST_ID)

@app.route("/sponsor/edit/", methods=["GET", "POST"])
@app.route("/sponsor/edit/<int:id>/", methods=["GET", "POST"])
@login_required
def configure_sponsor(id=None):
    if request.method == "POST":
        contacts = _extract_contacts(request.values, forms.EMAIL_BASENAME, forms.NAME_BASENAME)
        form = forms.SponsorForm(new=id is None)
        if form.validate_on_submit():
            sponsor = _configure_sponsor(id, form, contacts)
            return redirect(url_for("sponsor_info", id=sponsor.id))
    else:
        form = forms.SponsorForm(obj=model.Sponsor.query.get_or_404(id)) if id else forms.SponsorForm()
    contacts = model.Sponsor.query.get_or_404(id).contacts if id else []
    return render_template("configure-sponsor.html", id=id, form=form, contacts=contacts, email_basename=forms.EMAIL_BASENAME, name_basename=forms.NAME_BASENAME)

@app.route("/sponsor/<int:id>/edit/current-deal/", methods=["GET", "POST"])
@login_required
def edit_current_deal(id):
    if request.method == "POST":
        form = forms.CurrentDealForm()
        if form.validate_on_submit():
            _configure_deal(id, form)
            return redirect(url_for("sponsor_info", id=id))
    else:
        deal = model.Deal.query.filter_by(sponsor_id=id, year=datetime.date.today().year).first()
        form = forms.CurrentDealForm(obj=deal)
    
    return render_template("configure-deal.html", id=id, form=form, view="edit_current_deal")

@app.route("/sponsor/delete/", methods=["POST"])
@login_required
def delete_sponsor():
    id = request.form["sponsor-id"]
    model.db.session.delete(model.Sponsor.query.get_or_404(id))
    model.db.session.commit()
    return redirect(url_for("home"))
   

def _extract_contacts(data, email_basename, name_basename):
    emails, names = {}, {}
    for id in data:
        if id.startswith(email_basename) and forms.is_email(data[id]):
            emails[id.split('_')[-1]] = data[id]
        elif id.startswith(name_basename) and data[id] and data[id] != forms.NAME_BASENAME:
            names[id.split('_')[-1]] = data[id]
    
    return [(emails[index], names.get(index, emails[index].split('@')[0])) for index in emails]

def _configure_sponsor(id, form, contacts):
    if id:
        sponsor = model.Sponsor.query.get_or_404(id)
        sponsor.update_values(name=form.name.data, type_name=form.type_name.data, notes=form.notes.data, link=form.link.data, description=form.description.data)
    else:
        sponsor = model.Sponsor(form.name.data, type_name=form.type_name.data, notes=form.notes.data, link=form.link.data, description=form.description.data)
        model.db.session.add(sponsor)
    
    sponsor.set_contacts(contacts)
    
    model.db.session.commit()
    
    return sponsor

def _configure_deal(id, form):
    deal = model.Deal.query.filter_by(sponsor_id=id, year=form.year.data).first()
    if deal:
        deal.update_values(owner=form.owner.data, cash=form.cash.data, inkind=form.inkind.data, level_name=form.level_name.data)
    else:
        deal = model.Deal(id, datetime.date.today().year, form.owner.data, form.cash.data, form.inkind.data, form.level_name.data)
    
    model.db.session.commit()

def _configure_user(id, type_name, first_name, last_name, email, username):
    type_name = type_name.upper()
    
    if id:
        user = model.User.query.get_or_404(id)
        user.update_values(type_name=type_name, first_name=first_name, last_name=last_name, email=email, username=username)
    else:
        password = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        email = model.UserEmail(email=email, is_primary=True)
        auth = model.UserAuth(username=username, password=model.user_manager.hash_password(password))
        user = model.User(first_name=first_name, last_name=last_name, enabled=True, type_name=type_name, user_auth=auth)
        user.emails.append(email)
        model.db.session.add(user)
    
    model.db.session.commit()
    
    return user