from app import create_app, db, socketio
from app.auth.models import User
from app.admin_panel.models import Project, Task
from app.crowd_control.models import Session, LiveStatus, WorkerStatus, Worker, Message, Robot, \
                                     SpokenByUser, SpokenByRobot, RewardWaiting, DetailedStatus, Assignments, \
                                     SESSION_SQLALCHEMY, RewardActive
from sqlalchemy import exc
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask import session

# --------local testing----------------
if __name__ == "__main__":
    flask_app = create_app('dev')
    with flask_app.app_context():
        db.create_all()
    flask_app.run()
# ------------------------------------------

#-----------------PRODUCTION---------------------
# flask_app = create_app('dev')
#
# with flask_app.app_context():
#     db.create_all()
#     try:
#         if not User.query.filter_by(user_name='harry').first():
#             User.create_user(user='harry', email='harry@potters.com', password='secret')
#     except exc.IntegrityError:
#         # socketio = SocketIO(flask_app)
#         socketio.run(flask_app)
# #------------------------------------------------------
