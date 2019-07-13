from app.admin_panel import main
from app.media_manager import media_manager
from app import db
import datetime
# from app.admin_panel.models import Book, Publication
from flask import render_template, flash, request, redirect, url_for, jsonify
from flask import session as login_session
from app.auth import authentication as at
from flask_login import login_required
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, request, redirect, url_for, flash # for flash messaging

# from app.admin_panel.forms import EditBookForm, CreateBookForm

from sqlalchemy import exc,asc, desc, and_, or_, cast, Date

from app import OPENTOK_API_KEY, OPENTOK_TOKEN_ID, OPENTOK_SESSION_ID


@media_manager.route('/publish_video')
@login_required
def publish_screen():
    render_data = {
        "OPENTOK_API_KEY": OPENTOK_API_KEY,
        "OPENTOK_TOKEN_ID": OPENTOK_TOKEN_ID,
        "OPENTOK_SESSION_ID": OPENTOK_SESSION_ID
        }
    return render_template('publish_video.html', data = render_data)


@media_manager.route('/publish_audio')
@login_required
def publish_audio():
    render_data = {
        "OPENTOK_API_KEY": OPENTOK_API_KEY,
        "OPENTOK_TOKEN_ID": OPENTOK_TOKEN_ID,
        "OPENTOK_SESSION_ID": OPENTOK_SESSION_ID
        }
    return render_template('publish_audio.html', data = render_data)
