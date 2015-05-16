import datetime
import itertools
from collections import OrderedDict

from flask import redirect, render_template, request, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sponsortracker import model
from sponsortracker.data import UserType
from sponsortracker.dealtracker import forms
from sponsortracker.dealtracker.app import deal_tracker


DATE_FORMAT = "%a %b %d %Y"
REQUEST_ID = "request-date"

@deal_tracker.route("/")
@login_required
def my_accounts():
    if current_user.type != UserType.SALES.type:
        return redirect(url_for("dealtracker.all"))
        
    deals = model.Deal.query.filter_by(owner=current_user.user_auth.username, year=datetime.datetime.today().year).all()
    sponsors = [deal.sponsor for deal in deals]
    return render_template("sponsor-list.html", sponsors=sponsors)
    
@deal_tracker.route("/all/")
@login_required
def all():
    return render_template("sponsor-list.html", sponsors=model.Sponsor.query.all())

@deal_tracker.route("/sponsor/<int:id>/")
@login_required
def sponsor_info(id):
    sponsor = model.Sponsor.query.get_or_404(id)
    return render_template("sponsor-info.html", sponsor=sponsor, request_id=REQUEST_ID)

@deal_tracker.route("/sponsor/edit/", methods=["GET", "POST"])
@deal_tracker.route("/sponsor/<int:id>/edit/", methods=["GET", "POST"])
@login_required
def configure_sponsor(id=None):
    if request.method == "POST":
        contacts = _extract_contacts(request.values, forms.EMAIL_BASENAME, forms.NAME_BASENAME)
        form = forms.SponsorForm()
        
        print("NAME: \"" + form.name.data + "\"")
        
        if form.validate_on_submit():
            sponsor = _configure_sponsor(id, form, contacts)
            return redirect(url_for("dealtracker.sponsor_info", id=sponsor.id))
    else:
        form = forms.SponsorForm(obj=model.Sponsor.query.get_or_404(id)) if id else forms.SponsorForm()
    contacts = model.Sponsor.query.get_or_404(id).contacts if id else []
    return render_template("configure-sponsor.html", id=id, form=form, contacts=contacts, email_basename=forms.EMAIL_BASENAME, name_basename=forms.NAME_BASENAME)

@deal_tracker.route("/sponsor/<int:id>/edit/current-deal/", methods=["GET", "POST"])
@login_required
def edit_current_deal(id):
    if request.method == "POST":
        form = forms.CurrentDealForm()
        if form.validate_on_submit():
            _configure_deal(id, form)
            return redirect(url_for("dealtracker.sponsor_info", id=id))
    else:
        deal = model.Deal.query.filter_by(sponsor_id=id, year=datetime.date.today().year).first()
        form = forms.CurrentDealForm(obj=deal)
    
    return render_template("configure-deal.html", id=id, form=form, view="dealtracker.edit_current_deal")

@deal_tracker.route("/sponsor/delete/", methods=["POST"])
@login_required
def delete_sponsor():
    id = request.form["sponsor-id"]
    model.db.session.delete(model.Sponsor.query.get_or_404(id))
    model.db.session.commit()
    return redirect(url_for("dealtracker.my_accounts"))
   

def _extract_contacts(data, email_basename, name_basename):
    emails, names = {}, {}
    for id in data:
        if id.startswith(email_basename) and forms.validate_email(data[id]):
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
    
    if deal == deal.sponsor.current:
        deal.contract.ready = deal.cash > 0 or deal.inkind > 0
        deal.invoice.ready = deal.cash > 0 or deal.inkind > 0
        deal.asset_request.ready = bool(deal.level_name) and deal.contract.received
        
    model.db.session.commit()
