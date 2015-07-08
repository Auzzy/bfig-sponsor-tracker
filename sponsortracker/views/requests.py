import datetime

from flask import redirect, request, url_for
from flask.ext.login import current_user
from flask.ext.user import login_required

from sponsortracker import model
from sponsortracker.app import app

DATE_FORMAT = "%a %b %d %Y"
REQUEST_ID = "request-date"

@app.route("/sponsor/<int:id>/edit/contract-sent/", methods=["POST"])
@login_required
def contract_sent(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.contract, "sent", val))

@app.route("/sponsor/<int:id>/edit/contract-received/", methods=["POST"])
@login_required
def contract_received(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.contract, "received", val))

@app.route("/sponsor/<int:id>/edit/invoice-sent/", methods=["POST"])
@login_required
def invoice_sent(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.invoice, "sent", val))

@app.route("/sponsor/<int:id>/edit/invoice-received/", methods=["POST"])
@login_required
def invoice_received(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.invoice, "received", val))

@app.route("/sponsor/<int:id>/edit/asset-request-sent/", methods=["POST"])
@login_required
def asset_request_sent(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.asset_request, "sent", val))

@app.route("/sponsor/<int:id>/edit/asset-request-received/", methods=["POST"])
@login_required
def asset_request_received(id):
    return _update_request(id, lambda sponsor, val: setattr(sponsor.current.asset_request, "received", val))

def _update_request(sponsor_id, update_field):
    sponsor = model.Sponsor.query.get_or_404(sponsor_id)
    date = datetime.datetime.strptime(request.values[REQUEST_ID], DATE_FORMAT).date() if request.values.get(REQUEST_ID) else None
    update_field(sponsor, date)
    
    '''
    if sponsor.current.contract.received and not sponsor.current.contract.sent:
        sponsor.current.contract.received = None
    if sponsor.current.invoice.received and not sponsor.current.invoice.sent:
        sponsor.current.invoice.received = None
    if sponsor.current.asset_request.received and not sponsor.current.asset_request.sent:
        sponsor.current.asset_request.received = None
    '''
    
    # sponsor.current.asset_request.ready = bool(sponsor.current.level_name) and bool(sponsor.current.contract.received)
    
    model.db.session.commit()
    return redirect(url_for("sponsor_info", id=sponsor.id))
