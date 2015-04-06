import datetime
import itertools
from collections import OrderedDict

from flask import redirect, render_template, request, url_for
from flask.ext.user import roles_required
from flask.ext.login import current_user

from sponsortracker import model
from sponsortracker.data import RoleType
from sponsortracker.dealtracker import forms
from sponsortracker.dealtracker.app import deal_tracker

DATE_FORMAT = "%a %b %d %Y"
REQUEST_ID = "request-date"

@deal_tracker.route("/")
@roles_required([RoleType.DT_READ, RoleType.DT_WRITE])
def home():
    readonly = not current_user.has_roles(RoleType.DT_WRITE)
    return render_template("dealtracker.html", sponsors=model.Sponsor.query.all(), readonly=readonly)

@deal_tracker.route("/sponsor/<int:id>/")
@roles_required([RoleType.DT_WRITE])
def sponsor_info(id):
    sponsor = model.Sponsor.query.get_or_404(id)
    return render_template("sponsor-info.html", sponsor=sponsor, request_id=REQUEST_ID)

@deal_tracker.route("/sponsor/edit", methods=["GET", "POST"])
@deal_tracker.route("/sponsor/<int:id>/edit", methods=["GET", "POST"])
@roles_required([RoleType.DT_WRITE])
def configure_sponsor(id=None):
    if request.method == "POST":
        contacts = _extract_contacts(request.values, forms.EMAIL_BASENAME, forms.NAME_BASENAME)
        form = forms.SponsorForm()
        if form.validate_on_submit():
            sponsor = _configure_sponsor(id, form, contacts)
            return redirect(url_for("dealtracker.sponsor_info", id=sponsor.id))
    else:
        form = forms.SponsorForm(obj=model.Sponsor.query.get_or_404(id)) if id else forms.SponsorForm()
    contacts = model.Sponsor.query.get_or_404(id).contacts if id else []
    return render_template("configure-sponsor.html", id=id, form=form, contacts=contacts, email_basename=forms.EMAIL_BASENAME, name_basename=forms.NAME_BASENAME)

@deal_tracker.route("/sponsor/<int:id>/edit/current-deal", methods=["GET", "POST"])
@roles_required([RoleType.DT_WRITE])
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


@deal_tracker.route("/sponsor/<int:id>/edit/contract-sent", methods=["POST"])
def contract_sent(id):
    print("CONTRACT SENT")
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.contract, "sent", val))

@deal_tracker.route("/sponsor/<int:id>/edit/contract-received", methods=["POST"])
def contract_received(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.contract, "received", val))

@deal_tracker.route("/sponsor/<int:id>/edit/invoice-sent", methods=["POST"])
def invoice_sent(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.invoice, "sent", val))

@deal_tracker.route("/sponsor/<int:id>/edit/invoice-received", methods=["POST"])
def invoice_received(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.invoice, "received", val))

def _update_request(sponsor_id, update_field):
    sponsor = model.Sponsor.query.get_or_404(sponsor_id)
    date = datetime.datetime.strptime(request.values[REQUEST_ID], DATE_FORMAT).date() if request.values.get(REQUEST_ID) else None
    update_field(sponsor, date)
    if sponsor.current.contract.received and not sponsor.current.contract.sent:
        sponsor.current.contract.received = None
    if sponsor.current.invoice.received and not sponsor.current.invoice.sent:
        sponsor.current.invoice.received = None
    model.db.session.commit()
    return redirect(url_for("dealtracker.sponsor_info", id=sponsor.id))



@deal_tracker.route("/sponsor/delete", methods=["POST"])
@roles_required([RoleType.DT_WRITE])
def delete_sponsor():
    id = request.form["sponsor-id"]
    model.db.session.delete(model.Sponsor.query.get_or_404(id))
    model.db.session.commit()
    return redirect(url_for("dealtracker.home"))
    


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
        sponsor = model.Sponsor.query.get(id)
        sponsor.update(name=form.name.data, type_name=form.type_name.data, notes=form.notes.data)
    else:
        sponsor = model.Sponsor(form.name.data, type_name=form.type_name.data, notes=form.notes.data)
        model.db.session.add(sponsor)
    
    for contact in contacts:
        sponsor.add_contact(*contact)
    model.db.session.commit()
    
    return sponsor

def _configure_deal(id, form):
    deal = model.Deal.query.filter_by(sponsor_id=id, year=form.year.data).first()
    sponsor = model.Sponsor.query.get_or_404(id)
    if deal:
        deal.update(owner=form.owner.data, cash=form.cash.data, inkind=form.inkind.data)
    else:
        sponsor.add_deal(datetime.date.today().year, form.owner.data, form.cash.data, form.inkind.data)
    
    sponsor.update(level_name=form.level_name.data)
    
    if sponsor.current == deal:
        if deal.cash > 0 or deal.inkind > 0:
            deal.init_contract_invoice()
        
        if deal.cash == 0 and deal.inkind == 0:
            deal.remove_contract_invoice()
    
    model.db.session.commit()
