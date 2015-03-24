from flask.ext.mail import Message

from sponsortracker.app import mail
from sponsortracker.data import Level

'''
PARAMS TO INITIAL TEMPLATE
- deadline for submission
- sponsor level
- assets included in sponsorship level
- 
'''

'''
def _asset_description(asset):
    description = "One {spec.width}x{spec.height} {spec.unit.value} {label.what}"
    if asset.label.where:
        description += " in our {label.where}"
    return description.format(spec=asset.spec, label=asset.label)

def _send_initial(sponsor):
    asset_descriptions = []
    for asset in sponsor.level.assets:
        description = "One {spec.width}x{spec.height} {spec.unit.value} {what}".format(spec=asset.spec, what=asset.label.what)
        if asset.label.where:
            description += " in our {where}".format(where=asset.label.where)
        asset_descriptions.append(description)
        
    for description in asset_descriptions:
        print(description)

def _send_reminder(sponsor):
    asset_descriptions = []
    for asset in (sponsor.level.assets - sponsor.assets_by_type.keys()):
        description = asset.label.what
        if asset.label.where:
            description += " for our {where}".format(where=asset.label.where)
        asset_descriptions.append(description.lower())
        
    for description in asset_descriptions:
        print(description)
'''

def _plaintext_contents():
    pass

def _html_contents():
    pass

def send(sponsor):
    subject = "Development Email"
    recipients = ["bfigreceiver@gmail.com"]
    plaintext = "Hello.\nThis is a placeholder email during development, sent from the BFIG Sponsor Tracker.\n\nThanks."
    html = "<p>Hello.</p><p>This is a placeholder email during development, sent from the <strong>BFIG Sponsor Tracker.</strong></p><p>Thanks.</p>"
    
    return mail.send_message(
        subject=subject,
        recipients=recipients,
        body=plaintext,
        html=html,
        reply_to=None)