from app.crowd_control import crowd_control
from app.auth.models import User
from app import create_app, db
from sqlalchemy import exc,asc, desc, and_, or_
import datetime

from flask import session as login_session, json
import requests
from app.auth import authentication as at
from flask_login import login_required
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, request, redirect, url_for, flash # for flash messaging

# from app.crowd_control.forms import CreateNewProject, CreateNewTask
from app.admin_panel.models import Project, Task
from app.crowd_control.models import Session, LiveStatus, WorkerStatus, Worker, Message, Robot, \
                                     SpokenByUser, SpokenByRobot, RewardWaiting, DetailedStatus, Assignments, \
                                     SESSION_SQLALCHEMY, RewardActive



from flask import render_template, request, make_response, jsonify
from watson_developer_cloud import AuthorizationV1 as Authorization
from watson_developer_cloud import SpeechToTextV1 as SpeechToText
from watson_developer_cloud import IAMTokenManager

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement
from boto.mturk.price import Price

from oocsi import OOCSI

from app import socketio, STT_USERNAME, STT_PASSWORD, STT_APIKEY, STT_URL, endpoint_url, AMAZON_HOST
from app.crowd_control.events import isMovePossible, postJob
from app import socketio
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from app import create_app
from app import OPENTOK_API_KEY, OPENTOK_TOKEN_ID, OPENTOK_SESSION_ID

@crowd_control.route('/api/speech-to-text/token')
def getSttToken():
	print(STT_USERNAME)
	authorization = Authorization(username=STT_USERNAME, password=STT_PASSWORD)
	return authorization.get_token(url=SpeechToText.default_url)


#########################SNS############################
#https://blog.mturk.com/tutorial-using-amazon-sns-with-amazon-mturk-a0c6562717cb (FOR NECESSARY STEPS)
# https://gist.github.com/iMilnb/bf27da3f38272a76c801 (FOR CONFIRMATION)
######################################################
def msg_process(msg, tstamp):
    js = json.loads(msg)

    events = js['Events'][0]
    print(events)
    print(events['EventType'])

    if(events['EventType'] == 'AssignmentReturned'):
        status = 4 #returned
    if(events['EventType'] == 'AssignmentAbandoned'):
        status = 5 #abandoned

    try:
        if(events['EventType'] == 'HITCreated' or events['EventType'] == 'HITExpired'):
            print(events['EventType'])
        else:
            should_move = False
            w = Worker.query.filter_by(AMT_worker_id=events['WorkerId']).first()

            if w != None: #for example: it might be the case that queue is full and a new worker join, s/he will not be added into the queue, s/he might return
                          # the job but his/her record is not availbae in the DB beucase s/he might be a new user.
                live_status = LiveStatus.query.filter(LiveStatus.w_id == w.id).\
                                               filter(or_(LiveStatus.status_id == 1, LiveStatus.status_id == 2)).first()
                if live_status != None:
                    if live_status.status_id == 2: #we can only move one worker from waiting list if leaving worker was in active state
                        should_move = True

                    live_status.status_id = status

                    #add row to DetailedStatus Table
                    ds = DetailedStatus(live_status.id, status, datetime.datetime.utcnow())
                    db.session.add(ds)

                    #update Assignments table
                    assigns = Assignments.query.filter(Assignments.w_id==w.id).\
                                                filter(Assignments.hit_id==events['HITId']).\
                                                filter(Assignments.assign_id==events['AssignmentId']).first()
                    assigns.status_id = status

                    db.session.commit()

                    ########################################################
                    #Move one worker from waiting state to Active state
                    ########################################################

                    if should_move:
                        ################Fethcing Queue variables in advance###########
                        try:
                            s = Session.query.filter_by(status="Live").first()
                            task = db.session.query(Task).filter(Task.id==s.t_id).first()
                            # Max.Threshold values for ACTIVE and WAITING workers
                            MAX_ACTIVE = task.max_active
                            MAX_WAITING = task.max_waiting
                            #-------------------------------
                            #pre-conditions to start the job
                            #-------------------------------
                            MIN_ACTIVE = task.min_active
                            MIN_WAITING = task.min_waiting
                            #------------------------
                        except:
                            print('Error occured while fethcing Queue variable')

                        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
                        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()

                        precondition = SESSION_SQLALCHEMY.query.filter_by(id=3).first()

                        #You need to check whether any waiting worker can be moved to active list?
                        if isMovePossible(waiting_workers_count, active_workers_count, MAX_ACTIVE, MIN_WAITING) and precondition.Name == 'met':

                            l_s_worker = LiveStatus.query.filter_by(status_id=1).order_by(asc(LiveStatus.time_stamp)).first()

                            l_s_worker.status_id = 2 # add to active member list

                            worker = Worker.query.filter_by(id=l_s_worker.w_id).first()

                            socketio.emit('start_your_task', {'message': [worker.AMT_worker_id]}, namespace='/chat')

                            # s = Session.query.filter_by(status="Live").first() # grab active session

                            ds = DetailedStatus(l_s_worker.id, 2, datetime.datetime.utcnow())
                            db.session.add(ds)
                            db.session.commit()

                    #emit to tablet interface
                    # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
                    waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
                    active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
                    socketio.emit('workers_status', {'waiting': waiting_workers_count,
                                                    'active': active_workers_count},
                                                     namespace='/chat')

                        # postJob(s.t_id) # need to post a new job

    except exc.IntegrityError:
        pass

# socketio.on_event('custom even', msg_process, namespace='/chat')

@crowd_control.route('/stt')
def stt():
    return render_template("microphone-streaming-auto-stop.html")


@crowd_control.route('/tablet')
def tablet():
    try:
        # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
    except:
        # tutorial_workers_count = 0
        waiting_workers_count = 0
        active_workers_count = 0
    render_data = {'active': active_workers_count,
                  'waiting': waiting_workers_count}
    return render_template("tablet_display.html", name = render_data)


# do stuff here, like calling your favorite SMS gateway API
@crowd_control.route('/api/from_mturk', methods = ['GET', 'POST', 'PUT'])
def sns():
    # AWS sends JSON with text/plain mimetype

    js = json.loads(request.data)

    hdr = request.headers.get('X-Amz-Sns-Message-Type')
    # subscribe to the SNS topic
    if hdr == 'SubscriptionConfirmation' and 'SubscribeURL' in js:
        r = requests.get(js['SubscribeURL'])

    if hdr == 'Notification':
        msg_process(js['Message'], js['Timestamp'])

    return 'OK\n'

@crowd_control.route('/waiting_room', methods=['GET', 'POST'])
def waiting_room():

    try:
        active_task = Task.query.filter_by(task_status="Active").first()

        if active_task == None:
            instructions = "Not available"
            fix_price = 0.0
            task_id = 0
        else:
            fix_price = active_task.fix_price
            task_id = active_task.id

        #The following code segment can be used to check if the turker has accepted the task yet
        if request.args.get("assignmentId") == "ASSIGNMENT_ID_NOT_AVAILABLE":
            pass
        else:
            #get the worker ID and Assignment ID
            w_id = request.args.get("workerId")
            assign_id = request.args.get("assignmentId")

            # to access page without AMT for testing
            #----------------------------------------
            if w_id is None and assign_id is None:
                pass
           #-----------------------------------------
            else:
                pass

    except exc.IntegrityError:
        pass

    render_data = {
        "worker_id": request.args.get("workerId"),
        "assignment_id": request.args.get("assignmentId"),
        "amazon_host": AMAZON_HOST,
        "hit_id": request.args.get("hitId"),
        "some_info_to_pass": request.args.get("someInfoToPass"),
        "fix_price": fix_price,
        "task_id": task_id
    }

    resp = make_response(render_template("waiting_room.html", name = render_data))

    #This is particularly nasty gotcha.
    #Without this header, your iFrame will not render in Amazon
    resp.headers['x-frame-options'] = 'this_can_be_anything'
    return resp


######################----MAIN TASk -----############################

@crowd_control.route('/main_task', methods=['GET', 'POST'])
def main_task():

    active_task = Task.query.filter_by(task_status="Active").first()

    if active_task == None:
        fix_price = 0.0
    else:
        fix_price = active_task.fix_price

    render_data = {
    "worker_id": request.args.get("workerId"),
    "assignment_id": request.args.get("assignmentId"),
    "amazon_host": AMAZON_HOST,
    "hit_id": request.args.get("hitId"),
    "time_waited": request.args.get("time_waited"),
    "reward": request.args.get("reward"),
    "fix_price":fix_price,
    "OPENTOK_API_KEY": OPENTOK_API_KEY,
    "OPENTOK_TOKEN_ID": OPENTOK_TOKEN_ID,
    "OPENTOK_SESSION_ID": OPENTOK_SESSION_ID
    }

    return render_template("main_task.html", name = render_data)
