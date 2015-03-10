from flask import redirect, render_template, request, url_for
from flask.ext.user import roles_required
from flask.ext.login import current_user

from sponsortracker import model
from sponsortracker.data import RoleType
from sponsortracker.dealtracker import forms
from sponsortracker.dealtracker.app import deal_tracker

@deal_tracker.route("/")
@roles_required([RoleType.DT_READ, RoleType.DT_WRITE])
def home():
    readonly = not current_user.has_roles(RoleType.DT_WRITE)
    return render_template("dealtracker.html", sponsors=model.Sponsor.query.all(), readonly=readonly)

@deal_tracker.route("/sponsor/", methods=["GET", "POST"])
@deal_tracker.route("/sponsor/<int:id>/", methods=["GET", "POST"])
@roles_required([RoleType.DT_WRITE])
def configure_sponsor(id=None):
    if request.method == "POST":
        form = forms.SponsorForm()
        if form.validate_on_submit():
            _configure(id, form)
            return redirect(url_for("dealtracker.home"))
    else:
        form = forms.SponsorForm(obj=model.Sponsor.query.get_or_404(id)) if id else forms.SponsorForm()
    return render_template("sponsor.html", form=form, id=id)

@deal_tracker.route("/sponsor/delete", methods=["POST"])
@roles_required([RoleType.DT_WRITE])
def delete_sponsor():
    id = request.form["sponsor-id"]
    model.db.session.delete(model.Sponsor.query.get_or_404(id))
    model.db.session.commit()
    return redirect(url_for("dealtracker.home"))

def _configure(id, form):
    if id:
        sponsor = model.Sponsor.query.get(id)
        sponsor.update(name=form.name.data, email=form.email.data, level_name=form.level_name.data, cash=form.cash.data, inkind=form.inkind.data)
    else:
        sponsor = model.Sponsor(form.name.data, form.email.data, form.level_name.data, form.cash.data, form.inkind.data)
        model.db.session.add(sponsor)
    model.db.session.commit()
