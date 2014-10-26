from flask import Blueprint

deal_tracker = Blueprint('dealtracker', __name__, template_folder='templates', static_folder='static')