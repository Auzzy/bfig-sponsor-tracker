from flask import redirect, render_template, request, url_for

from sponsortracker.dealtracker import forms, sponsors
from sponsortracker.dealtracker.app import deal_tracker

@deal_tracker.route("/")
def home():
    sponsor_list = sponsors.load_all()
    return render_template("dealtracker.html", sponsors=sponsor_list)

@deal_tracker.route("/new-sponsor/", methods=["GET", "POST"])
@deal_tracker.route("/edit-sponsor/<int:id>/", methods=["GET", "POST"])
def configure_sponsor(id=None):
    if request.method == "POST":
        form = forms.SponsorForm()
        if form.validate_on_submit():
            sponsors.configure(id, form)
            return redirect(url_for("dealtracker.home"))
    else:
        form = sponsors.load(id).to_form() if id else forms.SponsorForm()
    return render_template("sponsor.html", form=form, id=id)

@deal_tracker.route("/delete-sponsor/<int:id>/")
def delete_sponsor(self, id):
    pass