import csv
import datetime
import itertools
import re

import os.path
import sys
sys.path += [os.path.abspath(os.path.pardir)]
from sponsortracker import data, model

VALUE_DELIMS = [';', ',', '&']
FILE = "leads.csv"
DEAL_YEAR_RE = re.compile("\((\d{4})\)")
EMAIL_RE = re.compile("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$")
YEAR_RE = re.compile("(\d{4})(?:\D|$)")


def _split_values(value_str):
    value = value_str.strip()
    for delim in VALUE_DELIMS:
        values = value.split(delim)
        if len(values) > 1:
            return [value.strip() for value in values]
    return [value]
    
def _map_values(value_str, years):
    value_map = {}
    for value in _split_values(value_str):
        deal_year = DEAL_YEAR_RE.search(value)
        if deal_year:
            value_map[deal_year.group(1)] = _remove_parens(value).strip() or 0
    
    if not value_map and len(years) == 1:
        value_map[years[0]] = _remove_parens(value_str).strip() or 0
    
    return value_map

def _remove_parens(value):
    while '(' in value:
        value = value[:value.find('(')] + value[value.find(')') + 1:]
    return value


def _notes(sponsor, row):
    sponsor.notes = row["Notes"].strip()

def _deals(sponsor, row):
    current_owner = row["New Acct Owner"].strip()
    sponsor.add_deal(datetime.date.today().year, owner=current_owner)
    
    years_val, owner_val, cash_val, inkind_val = row["Previous Sponsor?"], row["Previous Acct Owner"], row["Cash Amount Sponsored"], row["In Kind Sponsor"]
    
    years = YEAR_RE.findall(years_val)
    owner_map = _map_values(owner_val, years)
    cash_map = _map_values(cash_val.replace('$', '').replace(',', ''), years)
    inkind_map = _map_values(inkind_val.replace('$', '').replace(',', ''), years)
    
    for year in years:
        sponsor.add_deal(year, owner_map.get(year), cash_map.get(year, 0), inkind_map.get(year, 0))

def _contacts(sponsor, row):
    names = _split_values(_remove_parens(row["Contact Name"]))
    emails = _split_values(_remove_parens(row["Contact Email"]))
    
    for name, email in itertools.zip_longest(names, emails):
        if email:
            if EMAIL_RE.match(email):
                sponsor.add_contact(email, name)
            else:
                row["Notes"] =  "; {0}".format(email) if row["Notes"] else email

def _sponsor(row):
    name, type_val = row["Company"].strip(), row["Lead Type"].strip()
    
    type_name = data.SponsorType(type_val).name if type_val else None
    sponsor = model.Sponsor.query.filter_by(name=name).first()
    if sponsor:
        sponsor.update(type_name=type_name)
    else:
        sponsor = model.Sponsor(name, type_name=type_name)
        model.db.session.add(sponsor)
    return sponsor

def main(filename):
    with open(filename) as leads:
        for row in csv.DictReader(leads):
            print(row["Company"])
            sponsor = _sponsor(row)
            _contacts(sponsor, row)
            _deals(sponsor, row)
            _notes(sponsor, row)
    
    model.db.session.commit()

if __name__ == "__main__":
    main(FILE)
