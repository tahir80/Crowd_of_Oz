from app.admin_panel import main
from app.crowd_control import crowd_control
from app import db
import datetime
# from app.admin_panel.models import Book, Publication
from app.admin_panel.models import Project, Task
from app.crowd_control.models import LiveStatus, WorkerStatus, Worker, Message, Robot, \
                                     SpokenByUser, SpokenByRobot, RewardWaiting, Session, \
                                     DetailedStatus, Assignments, SESSION_SQLALCHEMY, RewardActive

from flask import render_template, flash, request, redirect, url_for, jsonify
from flask import session as login_session
from app.auth import authentication as at
from flask_login import login_required
from flask_login import login_user, logout_user, login_required, current_user
from flask import render_template, request, redirect, url_for, flash # for flash messaging

from app.admin_panel.forms import CreateNewProject, CreateNewTask, EditTask, MigrateWorkers
# from app.admin_panel.forms import EditBookForm, CreateBookForm

from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
from boto.mturk.qualification import Qualifications, PercentAssignmentsApprovedRequirement, NumberHitsApprovedRequirement
from boto.mturk.price import Price
from sqlalchemy import exc,asc, desc, and_, or_, cast, Date

from xml.dom.minidom import parseString

from app import connection #Mturk connection object

from app import socketio
from app import OPENTOK_API_KEY, OPENTOK_TOKEN_ID, OPENTOK_SESSION_ID

@main.route('/')
@login_required
def home():
    projects = Project.query.all()
    return render_template('home.html', projects = projects)


@main.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = CreateNewProject()
    #if data is validate, hten create a new project
    if form.validate_on_submit():
        Project.create_project(
        project_title = form.title.data,
        project_desc = form.Description.data,
        created_by = login_session['id'])

        flash('Project was Created Successfully!')
        return redirect(url_for('main.home'))
    return render_template('create_new_project.html', form = form)

@main.route('/create_task/<project_id>', methods=['GET', 'POST'])
@login_required
def create_task(project_id):
    form = CreateNewTask()
    if form.validate_on_submit():
        task = Task(project_id, "Not Active", form.hit_title.data, form.hit_desc.data,
                    form.keywords.data, form.fix_price.data, form.time_limit.data*60,
                     form.country.data, form.percent_approved.data,
                     form.HITS_approved.data, form.task_url.data, form.min_active.data,
                     form.min_waiting.data, form.max_active.data, form.max_waiting.data, datetime.datetime.utcnow())

        db.session.add(task)
        db.session.commit()

        flash('Task was Created Successfully!')
        return redirect(url_for('main.home'))
    return render_template('create_new_task.html', form = form)

@main.route('/list_tasks/<project_id>', methods=['GET', 'POST'])
@login_required
def list_tasks(project_id):
    tasks = db.session.query(Task).filter(Task.p_id==project_id).order_by(Task.id).all()
    return render_template('task_list.html', tasks = tasks)

@main.route('/post_task/<task_id>', methods=['GET', 'POST'])
@login_required
def postTask(task_id):

    task = db.session.query(Task).filter(Task.id==task_id).first()
    # taskinfo_session['task_id'] = task_id   #to retrieve task_id on the waiting room
    if task.task_status == "Active":
        flash('This Task is already Live!')
        return redirect(url_for('main.list_tasks', project_id=task.p_id))
    else:
        #frame_height in pixels
        frame_height = 800
        #This url will be the url of your application, with appropriate GET parameters
        url = task.task_url
        questionform = ExternalQuestion(url, frame_height).get_as_xml()
        create_hit_result = connection.create_hit(
            Title=task.title,
            Description=task.Description,
            Keywords=task.keywords,
            #duration is in seconds
            AssignmentDurationInSeconds = task.time_limit,
            #max_assignments will set the amount of independent copies of the task (turkers can only see one)
            MaxAssignments=task.max_active + task.max_waiting,
            Question=questionform,
            Reward=str(task.fix_price),
            LifetimeInSeconds = 60*60,
            AutoApprovalDelayInSeconds=60*60*72,
            # UniqueRequestToken='sjkdfsijdfgsidfuhsgidufg23234',
            QualificationRequirements=[
                    { 'QualificationTypeId': '000000000000000000L0',
                        'Comparator': 'GreaterThanOrEqualTo',
                        'IntegerValues': [task.approval_rate]
                    },
                    { 'QualificationTypeId': '00000000000000000040',
                        'Comparator': 'GreaterThanOrEqualTo',
                        'IntegerValues': [task.number_of_HITS]
                    },

                    { 'QualificationTypeId': '00000000000000000071',
                        'Comparator': 'In',
                        'LocaleValues':[{'Country':task.country}]
                        # 'LocaleValues':[{'Country':'US'}, {'Country':'IN'}]
                    }
                    ]
                )
            #https://docs.aws.amazon.com/AWSMechTurk/latest/AWSMturkAPI/ApiReference_QualificationRequirementDataStructureArticle.html#ApiReference_QualificationType-IDs
            # print(create_hit_result[0])
        flash('Task was posted Successfully to AMT!')
        # hit. = create_hit_result[0].HITTypeId
        task.HIT_Type_id = create_hit_result['HIT']['HITTypeId']
        task.task_status = "Active"
        session = Session(task.id, datetime.datetime.utcnow(), "Live")
        db.session.add(session)

        #need to hire workers automatically?
        server_session = SESSION_SQLALCHEMY.query.filter_by(id=2).first()
        server_session.Name = 'yes'

        #this variable was set to avoid premature moving of workers from waiting to active queue
        server_session = SESSION_SQLALCHEMY.query.filter_by(id=3).first()
        server_session.Name = 'not met'

        db.session.commit()


        # Simple Notification Service registration
        connection.update_notification_settings(
        HITTypeId = create_hit_result['HIT']['HITTypeId'],
        Notification = {
         'Destination': 'REPLACE_IT_WITH_YOUR_OWN_SNS_TOPIC',
         'Transport':'SNS',
         'Version':'2014-08-15',
         'EventTypes':['AssignmentAbandoned', 'AssignmentReturned',
                        'HITCreated', 'HITExpired'] })

        return redirect(url_for('main.list_tasks', project_id=task.p_id))





@main.route('/payments/<task_id>')
@login_required
def payments(task_id):
    try:

        s = Session.query.filter_by(t_id=task_id).first() # grab active session
        assigns = Assignments.query.filter(Assignments.s_id == s.id).\
                                    filter(or_(Assignments.status_id == 3, Assignments.status_id == 6)).all()

        active_task = Task.query.filter_by(id=task_id).first()
        table = []
        sum = 0
        for assign in assigns:
               row = []
               try:
                   response = connection.get_assignment(AssignmentId=assign.assign_id)
                   result = response['Assignment']
                   res = result['AssignmentStatus']
               except:
                   res = "Assignment Was not submitted"

               worker = Worker.query.filter_by(id=assign.w_id).first()

               reward_waiting = RewardWaiting.query.filter(RewardWaiting.s_id == s.id).\
                                                    filter(RewardWaiting.w_id == assign.w_id).first()

               reward_active = RewardActive.query.filter(RewardActive.s_id == s.id).\
                                                  filter(RewardActive.w_id == assign.w_id).first()

               if reward_waiting == None:
                   reward_queue = 0 # worker returned that job after joining the session in waiting
                   waited_queue = "00-00-00"
               else:
                   reward_queue = reward_waiting.reward
                   waited_queue = reward_waiting.waited_time
                   # continue

               if reward_active == None:
                    work_bonus = 0.0
                    time_bonus = 0.0
                    waited_time_active = "00-00-00"
                    no_of_msgs = 0
                    selected_msgs = 0
               else:
                   work_bonus = reward_active.work_based_bonus
                   time_bonus = reward_active.time_based_bonus
                   waited_time_active = reward_active.waited_time
                   no_of_msgs = reward_active.no_of_msgs
                   selected_msgs = reward_active.selected_msgs

               row.append(worker.id)
               row.append(worker.AMT_worker_id)
               row.append(assign.assign_id)
               row.append(assign.hit_id)
               row.append(active_task.fix_price)

               bonus = reward_queue + work_bonus + time_bonus
               bonus = round(bonus, 2)
               row.append(bonus)
               row.append(waited_queue)
               row.append(waited_time_active)
               row.append(s.id)
               row.append(task_id)
               row.append(no_of_msgs)
               row.append(selected_msgs)
               row.append(res)
               sum += active_task.fix_price + bonus

               table.append(row)

    except exc.IntegrityError:
        pass

    return render_template('payments.html', data=table, total_bonus=round(sum, 2))

@main.route('/approve/<assign_id>/<worker_id>/<bonus>/<session_id>/<task_id>')
@login_required
def approve(assign_id, worker_id, bonus, session_id, task_id):
    error_occured = False
    try:

        assign = Assignments.query.filter(Assignments.s_id == session_id).\
                               filter(Assignments.assign_id == assign_id).first()

        if assign.status_id == 6:
            flash('Already approved!')

        else:
            response = connection.approve_assignment(
            AssignmentId=assign_id,
            RequesterFeedback='Congratulations! Your HIT was approved.')

            print(response)
            if str(bonus) == '0.0':
                pass
            else:
                response = connection.send_bonus(
                WorkerId=worker_id,
                BonusAmount=str(bonus),
                AssignmentId=assign_id,
                Reason='Congratulations. You earned a bonus of amount = ' + bonus)

                print(response)

            assign.status_id = 6 #approved
            db.session.commit()

    except Exception as e:
        error_occured = True
        flash('An error was found while approving assignment')
        print(e)

    if not error_occured:
        flash('Assignment was Approved!')
    return redirect(url_for('main.payments', task_id=task_id))

@main.route('/reject/<assign_id>/<session_id>/<task_id>')
@login_required
def reject(assign_id, session_id, task_id):
    error_occured = False
    try:
        assign = Assignments.query.filter(Assignments.s_id == session_id).\
                               filter(Assignments.assign_id == assign_id).first()

        feedback = 'Sorry, Your work was not approved. You might have spent less time in either waiting or active stage or contributed less than the required threshold.If you have any doubts, please send an email to requester. We can revert the rejections!'

        response = connection.reject_assignment(
                    AssignmentId=assign_id,
                    RequesterFeedback=feedback)

        assign.status_id = 7 #rejected
        db.session.commit()

    except Exception as e:
        error_occured = True
        flash('An error was found while rejecting assignment')
        print(e)

    if not error_occured:
      flash('Assignment was Rejected Successfully!')
    return redirect(url_for('main.payments', task_id=task_id))

@main.route('/cloning/<task_id>/<project_id>', methods=['GET', 'POST'])
@login_required
def cloning(task_id, project_id):
    error_occured = False
    try:
        task = Task.query.filter(and_(Task.id==task_id, Task.p_id==project_id)).first()

        task = Task(project_id, "Not Active", task.title, task.Description,
                    task.keywords, task.fix_price, task.time_limit,
                    task.country, task.approval_rate,
                    task.number_of_HITS, task.task_url, task.min_active,
                    task.min_waiting, task.max_active, task.max_waiting, datetime.datetime.utcnow())

        db.session.add(task)
        db.session.commit()


    except:
        flash('Cloning was not successful!')
        error_occured = True
    if not error_occured:
        flash('Cloning was successful!')
    return redirect(url_for('main.list_tasks', project_id=task.p_id))


@main.route('/edit/<project_id>/<task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(project_id, task_id):
    task = Task.query.get(task_id)
    form = EditTask(obj=task)
    if request.method == 'GET':
        form.hit_title.data = task.title
        form.hit_desc.data = task.Description
        form.keywords.data = task.keywords
        form.fix_price.data = task.fix_price
        form.time_limit.data = int(task.time_limit / 60)
        form.country.data  = task.country
        form.percent_approved.data = task.approval_rate
        form.HITS_approved.data = task.number_of_HITS
        form.task_url.data = task.task_url
        form.min_active.data = task.min_active
        form.min_waiting.data = task.min_waiting
        form.max_active.data = task.max_active
        form.max_waiting.data = task.max_waiting
    if form.validate_on_submit():
        task.title = form.hit_title.data
        task.Description = form.hit_desc.data
        task.keywords = form.keywords.data
        task.fix_price = form.fix_price.data
        task.time_limit = form.time_limit.data*60
        task.country =  form.country.data
        task.approval_rate = form.percent_approved.data
        task.number_of_HITS = form.HITS_approved.data
        task.task_url = form.task_url.data
        task.min_active = form.min_active.data
        task.min_waiting = form.min_waiting.data
        task.max_active = form.max_active.data
        task.max_waiting = form.max_waiting.data
        db.session.add(task)
        db.session.commit()
        flash('Task Edited Successfully')
        return redirect(url_for('main.list_tasks', project_id=task.p_id))
    return render_template('edit_task.html', form=form)

@main.route('/migrate/<project_id>/<task_id>', methods=['GET', 'POST'])
@login_required
def migrate_workers(project_id, task_id):

    form = MigrateWorkers()

    if form.validate_on_submit():

        #update the starting condition.
        server_session = SESSION_SQLALCHEMY.query.filter_by(id=3).first()
        server_session.Name = 'met'
        db.session.commit()

        #fetch latest workers
        workers = LiveStatus.query.filter_by(status_id=1).order_by(asc(LiveStatus.time_stamp)).all()

        workers_list = []
        count = 0
        for worker_status in workers:

            if count >= form.NumberOfWorkers.data:
                break

            #change status of workers from 'waiting' to 'active'
            worker_status.status_id = 2
            w_ids = Worker.query.filter_by(id=worker_status.w_id).first()

            #append workers to list (this was done to send message to only specific/active clients)
            workers_list.append(w_ids.AMT_worker_id)

            #also add rows to DetailedStatus table Here
            ds = DetailedStatus(worker_status.id, 2, datetime.datetime.utcnow())
            db.session.add(ds)
            db.session.commit()

            count += 1

        socketio.emit('start_your_task', {'message': workers_list}, namespace='/chat')
        socketio.emit('pepper_receiver', {'sender': "crowd", 'message': "Hello, I am Pepper. I am ready to talk with you. How can I help you?"}, namespace='/chat')
        socketio.emit('display_to_tablet', {'text': "Hello, I am Pepper. I am ready to talk with you. How can I help you?"}, namespace='/chat')

        waiting_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 1).count()
        active_workers_count = LiveStatus.query.filter(LiveStatus.status_id == 2).count()
        socketio.emit('workers_status', {'waiting': waiting_workers_count,
                                'active': active_workers_count},
                                  namespace='/chat')


    return render_template('migrate_workers.html', form=form)
