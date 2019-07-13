from app import db
from app.auth.models import User
from app.admin_panel.models import Project, Task
from app.crowd_control.models import Session, LiveStatus, WorkerStatus, Worker, Message, Robot, \
                                      SpokenByUser, SpokenByRobot, RewardWaiting, DetailedStatus, Assignments, SESSION_SQLALCHEMY, \
                                      RewardActive, Tutorial

from app.crowd_control import crowd_control

from sqlalchemy import exc,asc, desc, and_, or_
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
from flask import session, request
from flask import render_template, request, redirect, url_for, flash # for flash messaging
from app import socketio
import datetime

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement
from boto.mturk.price import Price
import boto3

from app import connection, connection2


@socketio.on('expireHIT', namespace='/chat')
def expireHIT(data):

    #here you need to write code for HIT expireation
    s = Session.query.filter_by(status="Live").first()

    assigns = db.session.query(Assignments.hit_id).\
                            filter(Assignments.s_id == s.id).\
                            distinct()

    for assign in assigns:
        print(assign.hit_id)
        try:
            response = connection.update_expiration_for_hit(
            HITId=assign.hit_id,
            ExpireAt=datetime.datetime(2015, 1, 1))
        except:
            print("an error occured for hitID!", assign.hit_id)

    #here you can change the task + session table
    s.s_end_time = datetime.datetime.utcnow()
    s.status = "expired"

    task = db.session.query(Task).filter(Task.id==data['taskID']).first()
    task.task_status = "Not Active"
    db.session.commit()


@socketio.on('stop_this_job', namespace='/chat')
def stopJob(data):
    try:

        server_session = SESSION_SQLALCHEMY.query.filter_by(id=2).first()
        server_session.Name = 'no'

        precondition_met = SESSION_SQLALCHEMY.query.filter_by(id=3).first()
        precondition_met.Name = 'not met'

        db.session.commit()
    except:
        pass

    emit('stop', {}, broadcast = True)


@socketio.on('fromcrowd', namespace='/chat')
def fromcrowd(data):
    try:
        s = Session.query.filter_by(status="Live").first()
        worker = db.session.query(Worker).filter(Worker.AMT_worker_id==data['worker']).first() # get the worker info from DB
        msg = Message(s.id, data['message'], datetime.datetime.utcnow())
        db.session.add(msg)
        db.session.flush() # for getting ID's back

        #Since we allowed duplicate workers to work on our task, we carefully need to grab the latest worker from the current session added into
        #the table. Another solution is to refer assign ID from both tables (rewards) --> require changes in schema
        latest_active_reward = RewardActive.query.filter(and_(RewardActive.w_id==worker.id, RewardActive.s_id==s.id)).order_by(desc(RewardActive.time_stamp)).first()
        latest_active_reward.no_of_msgs += 1
        latest_active_reward.work_based_bonus += 0.02 #grab these values from DB in future

        server_session = SESSION_SQLALCHEMY.query.filter_by(id=1).first()
        if server_session.Name == "User_Said_Something":

            #first send respose to pepper through socketIO bridge (HTML client)
            emit('pepper_receiver', {'sender': "crowd", 'message': data['message']}, broadcast = True)

            #emit to crowd interface
            emit('display_crowd_response', {'worker':data['worker'], 'message': data['message']}, broadcast = True)

            #emit to Tablet on robot
            emit('display_to_tablet', {'text': data['message']}, broadcast = True)

            #this will update chat on all waiting screens
            emit('update_chat', {'from': "Robot", 'message': data['message']}, broadcast = True)

            # emit('waiting_crowd', {'from': 'Crowd', 'message': data['message']}, broadcast = True)

            #change status so that no other crowd responses reach to Pepper
            server_session.Name = "nothing"
            #add (Tag = YES) if the message is selected by server
            sbr = SpokenByRobot(worker.id, msg.id, "YES", datetime.datetime.utcnow(), data['msgType'])
            db.session.add(sbr)

            latest_active_reward.selected_msgs += 1
            #in addition to usual pay per contribution, we have to pay extra for selected responses
            latest_active_reward.work_based_bonus += 0.03 #grab these values from DB in future
        else:
            #add (tag = False) if the message is not selected
            sbr = SpokenByRobot(worker.id, msg.id, "NO", datetime.datetime.utcnow(), data['msgType'])
            db.session.add(sbr)

        db.session.commit() #commit everything at the end

        #sendback response to the client to update Score
        emit('update_score', {'workerId': data['worker'],
                              'total_msgs': latest_active_reward.no_of_msgs,
                              'selected_msgs': latest_active_reward.selected_msgs,
                              'bonus': latest_active_reward.work_based_bonus}, broadcast = True)
    except exc.IntegrityError:
        pass


@socketio.on('frompepper', namespace='/chat')
def frompepper(data):
    message = ""
    if data['message'] == 'ERROR':
        emit('display_to_tablet', {'text': "Sorry, I didn't recognize your voice. But you don't need to speak again!"}, broadcast = True)
        # emit('fromuser', {'message': "Voice was not transcribed correctly. Please suggest a valid response about what you heard."}, broadcast = True)
        message = "Voice was not transcribed correctly. Please suggest a valid response about what you heard."
    else:
        message = data['message']
    try:

        if not Robot.query.filter_by(Name=data['Name']).first():
            Robot.create_robot(Name=data['Name'])

        #emit message to all clients first
        emit('fromuser', {'message': message}, broadcast = True)

        if data['message'] != 'ERROR':
            emit('display_to_tablet', {'text': message}, broadcast = True)

        # emit('waiting_crowd', {'from': 'User', 'message': data['message']}, broadcast = True)

        # #Grab the Session variable from SESSION_SQLALCHEMY table
        # server_session = SESSION_SQLALCHEMY.query.filter_by(id=1).first()
        # #add the Tag so that we can check whether user said something?
        # server_session.Name = "User_Said_Something"

        robot = db.session.query(Robot).filter(Robot.Name==data['Name']).first()
        s = Session.query.filter_by(status="Live").first()
        if s == None:
            pass
        else:
            msg = Message(s.id, message, datetime.datetime.utcnow())
            db.session.add(msg)

            db.session.flush() # for getting ID back

            sbu = SpokenByUser(robot.id, msg.id,datetime.datetime.utcnow())
            db.session.add(sbu)
            db.session.commit()
    except exc.IntegrityError:
        pass


    #this will update chat on all waiting screens
    emit('update_chat', {'from': "User", 'message': data['message'].strip('\n')}, broadcast = True)

@socketio.on('user_started_speaking', namespace='/chat')
def userStartedSpeaking(data):
    #Grab the Session variable from SESSION_SQLALCHEMY table
    server_session = SESSION_SQLALCHEMY.query.filter_by(id=1).first()
    #add the Tag so that we can check whether user said something?
    server_session.Name = "User_Said_Something"
    db.session.commit()

    # emit('start_progress_bar', {}, broadcast = True)
    # emit('enable_send_button', {}, broadcast = True)


@socketio.on('user_stopped_speaking', namespace='/chat')
def userStoppedSpeaking(data):
    emit('start_progress_bar', {}, broadcast = True)


@socketio.on('connected', namespace='/chat')
def connected(data):
    # isInitialConditionMet = False  # this flag will prevent premature moving waiting workers until precondition meets.
    try:

        ##Write a code to determine whether a same user with same status wants to re-join the session again? it might be due to page reload..
       duplicate = False
       worker = Worker.query.filter_by(AMT_worker_id=data['workerId']).first()

       if worker != None: # that means worker already exists in our worker's list. If value is None, then its a brand new worker and duplicate remains False
            s = Session.query.filter_by(status="Live").first() # grab live session
            status = LiveStatus.query.filter(LiveStatus.s_id == s.id).\
                                      filter(LiveStatus.w_id == worker.id).\
                                      filter(or_(LiveStatus.status_id == 1,LiveStatus.status_id == 2)).first()
            if status != None:
                if status.status_id == 1 or status.status_id == 2:
                    print(status.status_id)
                    duplicate = True
       print(duplicate)

       if not duplicate:

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
               print('max_active', MAX_ACTIVE)
               print('max_waiting', MAX_WAITING)
               print('min_active', MIN_ACTIVE)
               print('min_waiting', MIN_WAITING)

            except:
                print('Error occured while fethcing Queue variable')

            waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
            active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
            print('waiting_workers_count', waiting_workers_count)
            print('active_workers_count', active_workers_count)
            #This condition will only be executed at the start, when workers reach min.threshold value and active
            # workers are still empty.
            if waiting_workers_count == MIN_ACTIVE and active_workers_count == 0:

                server_session = SESSION_SQLALCHEMY.query.filter_by(id=3).first()
                server_session.Name = 'met'
                db.session.commit()

                records = LiveStatus.query.filter(LiveStatus.status_id == 1).all()
                workers_list = []
                for worker_status in records:
                    #change status of workers from 'waiting' to 'active'
                    worker_status.status_id = 2
                    w_ids = Worker.query.filter_by(id=worker_status.w_id).first()

                    #append workers to list (this was done to send message to only specific/active clients)
                    workers_list.append(w_ids.AMT_worker_id)

                    #also add rows to DetailedStatus table Here
                    ds = DetailedStatus(worker_status.id, 2, datetime.datetime.utcnow())
                    db.session.add(ds)
                    db.session.commit()

                emit('start_your_task', {'message': workers_list}, broadcast = True)
                emit('pepper_receiver', {'sender': "crowd", 'message': "Hello, I am Pepper. I am ready to talk with you. How can I help you?"}, broadcast = True)
                emit('display_to_tablet', {'text': "Hello, I am Pepper. I am ready to talk with you. How can I help you?"}, broadcast = True)

            # cannot accept more workers. This situation will never reach in reality (we will post the job according to waiting + active)
            if waiting_workers_count == MAX_WAITING and active_workers_count == MAX_ACTIVE:
                emit('job_is_full', {'message': "Sorry, this Job is already full. Please try later", 'id': data['workerId']}, broadcast = True)

            #store worker to DB and update live status.
            #only store data if job is not full
            if waiting_workers_count != MAX_WAITING or active_workers_count != MAX_ACTIVE:

                if not Worker.query.filter_by(AMT_worker_id=data['workerId']).first():
                    worker = Worker(data['workerId'])
                    db.session.add(worker)
                    db.session.flush()
                else:
                    worker = Worker.query.filter_by(AMT_worker_id=data['workerId']).first()
                #grab an active session
                current_session = Session.query.filter_by(status="Live").first()

                # hits = HITS.query.filter_by(s_id=current_session.id).order_by(desc(HITS.time_stamp)).first()

                assign = Assignments(worker.id, data['hit_id'], data['aid'], current_session.id, datetime.datetime.utcnow())
                db.session.add(assign)

                live_status = LiveStatus(worker.id, current_session.id, 1, datetime.datetime.utcnow())

                db.session.add(live_status)
                db.session.flush()
                #add row to DetailedStatus Table
                ds = DetailedStatus(live_status.id, 1, datetime.datetime.utcnow())
                db.session.add(ds)
                #save changes
                db.session.commit()

                #You need to check whether any waiting worker can be moved to active list?
                waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
                active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()

                precondition = SESSION_SQLALCHEMY.query.filter_by(id=3).first()

                if isMovePossible(waiting_workers_count, active_workers_count, MAX_ACTIVE, MIN_WAITING) and precondition.Name == 'met':

                    l_s_worker = LiveStatus.query.filter_by(status_id=1).order_by(asc(LiveStatus.time_stamp)).first()

                    l_s_worker.status_id = 2 # add to active member list

                    ds = DetailedStatus(l_s_worker.id, 2, datetime.datetime.utcnow())
                    db.session.add(ds)
                    db.session.commit()
                    # live_status_workers = LiveStatus.query.filter_by(status_id=1).all()
                    # l_s_worker = live_status_workers.order_by(asc(live_status_workers.time_stamp)).limit(1).first()
                    worker = Worker.query.filter_by(id=l_s_worker.w_id).first()
                    emit('start_your_task', {'message': [worker.AMT_worker_id]}, broadcast = True)


            #emit to tablet interface
            # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
            waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
            active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
            emit('workers_status', {'waiting': waiting_workers_count,
                                    'active': active_workers_count},
                                     broadcast = True)

            # update notice board with worker count
            workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
            emit('update_worker_count', {'count': workers_count, 'max_count': MAX_WAITING}, broadcast = True)


            #You need to show Message History for new Workers
            s = Session.query.filter_by(status="Live").first() # grab live session
            sbu = SpokenByUser.query.all() # grab all messages spoken by user
            sbr = SpokenByRobot.query.filter(SpokenByRobot.is_selected == 'YES').all() #grab all selected messages from crowd

            #select all messages from Message table if message ids are available either in SpokenByUser or SpokenByRobot provided that Live session is selected
            messages = Message.query.filter(s.id == Message.s_id).\
                                     filter(or_(Message.id.in_([x.m_id for x in sbu]), Message.id.in_([y.m_id for y in sbr]))).\
                                     order_by(Message.time_stamp).all()
            m_list = []
            for msg in messages:
                if msg.id in [x.m_id for x in sbu]:
                    m_list.append("User: "+ msg.text.strip('\n'))
                else:
                    m_list.append("Robot: "+msg.text.strip('\n'))

            emit('show_message_histoy', {'worker': data['workerId'], 'msgs': m_list}, broadcast = True)

    except exc.IntegrityError:
        pass

@socketio.on('IAmReady', namespace='/chat')
def client_is_ready(data):
    workerId = data['worker']
    time_waited = data['time_waited']
    reward = data['reward']

    try:
        s = Session.query.filter_by(status="Live").first()
        w = Worker.query.filter_by(AMT_worker_id=workerId).first()
        reward_waiting = RewardWaiting(w.id, s.id,reward,time_waited)
        reward_active = RewardActive(w.id, s.id,0)
        db.session.add(reward_waiting)
        db.session.add(reward_active)
        db.session.commit()
    except exc.IntegrityError:
        pass

@socketio.on('submit_waiting', namespace='/chat')
def submit_waiting(data):

    workerId = data['worker']
    time_waited = data['time_waited']
    reward = data['reward']
    assignId = data['aid']
    hitId = data['hit_id']
        # Save Reward related data
    try:
        s = Session.query.filter_by(status="Live").first()
        w = Worker.query.filter_by(AMT_worker_id=workerId).first()
        reward_waiting = RewardWaiting(w.id, s.id,reward,time_waited)
        db.session.add(reward_waiting)
        #change status from 'waiting' --> 'submitted', only select worker who is waiting
        live_status = LiveStatus.query.filter(and_(LiveStatus.w_id == w.id, LiveStatus.status_id == 1)).first()
        # live_status = LiveStatus.query.filter_by(w_id=w.id).first()
        live_status.status_id = 3

        #add row to DetailedStatus Table
        ds = DetailedStatus(live_status.id, 3, datetime.datetime.utcnow())
        db.session.add(ds)

        #update Assignments table
        assigns = Assignments.query.filter(Assignments.w_id==w.id).\
                                    filter(Assignments.hit_id==hitId).\
                                    filter(Assignments.assign_id==assignId).first()
        assigns.status_id = 3

        db.session.commit()

        #emit to tablet interface
        # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
        emit('workers_status', {'waiting': waiting_workers_count,
                                'active': active_workers_count},
                                 broadcast = True)
    except exc.IntegrityError:
        pass

    #Post a new Job, first check whether admin has pressed the 'stop' button? if admin press the stop
    #button then the value of name would be 'no' and posting a job would be skipped.
    server_session = SESSION_SQLALCHEMY.query.filter_by(id=2).first()
    if server_session.Name == 'yes':
        postJob(s.t_id)

@socketio.on('submit_active', namespace='/chat')
def submit_active(data):
    workerId = data['worker']
    assignId = data['aid']
    hitId = data['hit_id']

    try:

        ############STEP #1: Change the status of worker who submit the job#########################
        s = Session.query.filter_by(status="Live").first()
        w = Worker.query.filter_by(AMT_worker_id=workerId).first()
        # reward_waiting = RewardWaiting(w.id, s.id,reward,time_waited)
        # db.session.add(reward_waiting)
        #change status from 'waiting' --> 'submitted', only select worker who is waiting
        live_status = LiveStatus.query.filter(and_(LiveStatus.w_id == w.id, LiveStatus.status_id == 2)).first()
        # live_status = LiveStatus.query.filter_by(w_id=w.id).first()
        live_status.status_id = 3

        #add row to DetailedStatus Table
        ds = DetailedStatus(live_status.id, 3, datetime.datetime.utcnow())
        db.session.add(ds)

        #update Assignments table
        assigns = Assignments.query.filter(Assignments.w_id==w.id).\
                                    filter(Assignments.hit_id==hitId).\
                                    filter(Assignments.assign_id==assignId).first()
        assigns.status_id = 3

        #update the RewardActive Table with total waiting time  + time based Bonus (Duplicate workers: again only latest worker from the current session)
        reward_active = RewardActive.query.filter(and_(RewardActive.w_id==w.id, RewardActive.s_id==s.id)).order_by(desc(RewardActive.time_stamp)).first()
        reward_active.waited_time = data['time_waited']
        reward_active.time_based_bonus = 0.0

        db.session.commit()

        ##############################################################################################
        #Step # 2: Move one worker from waiting state to Active state
        #############################################################################################
        # MAX_ACTIVE = 3
        # MAX_WAITING = 3
        # MIN_ACTIVE = 2
        # MIN_WAITING = 1

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
            print('max_active', MAX_ACTIVE)
            print('max_waiting', MAX_WAITING)
            print('min_active', MIN_ACTIVE)
            print('min_waiting', MIN_WAITING)

        except:
            print('Error occured while fethcing Queue variable')

        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
        print('waiting_workers_count', waiting_workers_count)
        print('active_workers_count', active_workers_count)
        #You need to check whether any waiting worker can be moved to active list?
        if isMovePossible(waiting_workers_count, active_workers_count, MAX_ACTIVE, MIN_WAITING):
            print('yes, move is possible')

            l_s_worker = LiveStatus.query.filter_by(status_id=1).order_by(asc(LiveStatus.time_stamp)).first()

            l_s_worker.status_id = 2 # add to active member list

            ds = DetailedStatus(l_s_worker.id, 2, datetime.datetime.utcnow())
            db.session.add(ds)
            db.session.commit()
            worker = Worker.query.filter_by(id=l_s_worker.w_id).first()
            emit('start_your_task', {'message': [worker.AMT_worker_id]}, broadcast = True)

        #emit to tablet interface
        try:
            # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
            waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
            active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
        except:
            if waiting_workers_count == None:
                waiting_workers_count = 0
            if active_workers_count == None:
                active_workers_count = 0
            # if tutorial_workers_count == None:
            #     tutorial_workers_count = 0

        emit('workers_status', {'waiting': waiting_workers_count,
                                'active': active_workers_count},
                                 broadcast = True)

    except exc.IntegrityError:
        pass

    #Step 3:Post a new Job ###################################################
    #Post a new Job, first check whether admin has pressed the 'stop' button? if admin press the stop
    #button then the value of name would be 'no' and posting a job would be skipped.
    server_session = SESSION_SQLALCHEMY.query.filter_by(id=2).first()
    if server_session.Name == 'yes':
        postJob(s.t_id)

@socketio.on('start_tutorial', namespace='/chat')
def start_tutorial(data):
    workerId = data['workerId']
    aid = data['aid']
    hit_id = data['hit_id']

    try:
        if isFull():
            emit('job_is_full', {'message': "Sorry, this Job is currently full. Please try it later", 'id': data['workerId']}, broadcast = True)
        else:
           duplicate = False
           worker = Worker.query.filter_by(AMT_worker_id=data['workerId']).first()

           if worker != None:
                s = Session.query.filter_by(status="Live").first()
                status = LiveStatus.query.filter(LiveStatus.s_id == s.id).\
                                          filter(LiveStatus.w_id == worker.id).\
                                          filter(LiveStatus.status_id == 0).first()
                if status != None:
                    if status.status_id == 0:
                        duplicate = True
           if duplicate:
               pass
           else:
                if not Worker.query.filter_by(AMT_worker_id=data['workerId']).first():
                    worker = Worker(data['workerId'])
                    db.session.add(worker)
                    db.session.flush()
                else:
                    worker = Worker.query.filter_by(AMT_worker_id=data['workerId']).first()

                current_session = Session.query.filter_by(status="Live").first()

                assign = Assignments(worker.id, data['hit_id'], data['aid'], current_session.id, datetime.datetime.utcnow())
                db.session.add(assign)

                live_status = LiveStatus(worker.id, current_session.id, 0, datetime.datetime.utcnow())

                db.session.add(live_status)
                db.session.flush()
                #add row to DetailedStatus Table
                ds = DetailedStatus(live_status.id, 0, datetime.datetime.utcnow())
                db.session.add(ds)
                #save changes
                db.session.commit()

                #emit to tablet interface
                # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
                waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
                active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
                emit('workers_status', {'waiting': waiting_workers_count,
                                        'active': active_workers_count},
                                         broadcast = True)

    except:
        pass

@socketio.on('isJobFull', namespace='/chat')
def isJobFull(data):
    if isFull():
        emit('job_is_full', {'message': "Sorry, this Job is currently full. Please try later", 'id': data['workerId']}, broadcast = True)


@socketio.on('submit_tutorial', namespace='/chat')
def submit_tutorial(data):
    print('submit_tutorial was called')
    workerId = data['worker']
    assignId = data['aid']
    hitId = data['hit_id']

    try:

        ############STEP #1: Change the status of worker who submit the job#########################
        s = Session.query.filter_by(status="Live").first()
        w = Worker.query.filter_by(AMT_worker_id=workerId).first()
        # reward_waiting = RewardWaiting(w.id, s.id,reward,time_waited)
        # db.session.add(reward_waiting)
        #change status from 'waiting' --> 'submitted', only select worker who is waiting
        live_status = LiveStatus.query.filter(and_(LiveStatus.w_id == w.id, LiveStatus.status_id == 0)).first()
        # live_status = LiveStatus.query.filter_by(w_id=w.id).first()
        live_status.status_id = 3

        #add row to DetailedStatus Table
        ds = DetailedStatus(live_status.id, 3, datetime.datetime.utcnow())
        db.session.add(ds)

        #update Assignments table
        assigns = Assignments.query.filter(Assignments.w_id==w.id).\
                                    filter(Assignments.hit_id==hitId).\
                                    filter(Assignments.assign_id==assignId).first()
        assigns.status_id = 3
        db.session.commit()

    except:
        pass

    #emit to tablet interface
    try:
        # tutorial_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 0).count()
        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
    except:
        if waiting_workers_count == None:
            waiting_workers_count = 0
        if active_workers_count == None:
            active_workers_count = 0
        # if tutorial_workers_count == None:
        #     tutorial_workers_count = 0

    emit('workers_status', {'waiting': waiting_workers_count,
                            'active': active_workers_count},
                             broadcast = True)



def isFull():
    try:
        s = Session.query.filter_by(status="Live").first()
        task = db.session.query(Task).filter(Task.id==s.t_id).first()

        MAX_ACTIVE = task.max_active
        MAX_WAITING = task.max_waiting

        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()

        if waiting_workers_count == None:
            waiting_workers_count = 0
        if active_workers_count == None:
            active_workers_count = 0

        if waiting_workers_count == MAX_WAITING and active_workers_count == MAX_ACTIVE:
            return True
        else:
            return False
    except:
        return False


def postJob(task_id):


    hit = db.session.query(Task).filter(Task.id==task_id).first()

    ##############################################################
    #source: https://github.com/numaer/psyturk/blob/master/hits.py
    #############################################################
    connection.create_hit_with_hit_type(
    HITTypeId = hit.HIT_Type_id,
    MaxAssignments = 1,
    LifetimeInSeconds = hit.hit_expiry,
    Question = ExternalQuestion(hit.task_url, 800).get_as_xml())


def isMovePossible(waiting, active, max_active, min_waiting):

    # if active == 0:
    #     return False

    if (waiting - 1) > (min_waiting - 1) and (active + 1) <= max_active:
        return True
    else:
        return False
