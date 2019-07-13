from flask import Blueprint

crowd_control = Blueprint('crowd_control', __name__ , template_folder='templates')

from app.crowd_control import routes, events
