from flask import Blueprint


media_manager = Blueprint('media_manager', __name__ , template_folder='templates')

from app.media_manager import routes
