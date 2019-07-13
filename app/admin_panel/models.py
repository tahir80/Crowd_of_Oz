from app import db # we already defined db instance inside app/__init__.py file
import datetime
from app.auth.models import User
#
#
#
###################Project#####################################
class Project(db.Model):
    __tablename__ = 'Project'

    id = db.Column(db.Integer, primary_key = True)
    project_title = db.Column(db.String(100), nullable = False)
    project_desc = db.Column(db.String(500), nullable = False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    date_created = db.Column(db.DateTime, default = datetime.datetime.now())

    def __init__(self, project_title, project_desc, created_by):
            self.project_title = project_title
            self.project_desc = project_desc
            self.created_by = created_by

    def __repr__(self):
        return 'Project Title:'.format(self.project_title)

    @classmethod
    def create_project(cls, project_title, project_desc, created_by):
        project = cls(project_title=project_title,
                      project_desc = project_desc,
                      created_by = created_by)

        db.session.add(project)
        db.session.commit()
        return project

################## TASK class ##############################
class Task(db.Model):
    __tablename__ = 'Task'

    id = db.Column(db.Integer, primary_key = True)

    #relationship with project
    p_id = db.Column(db.Integer, db.ForeignKey('Project.id'))

    HIT_Type_id = db.Column(db.String(100), nullable = True)  # generated by AMT
    task_status = db.Column(db.String(100), nullable = False)

    #Mandatory fields
    title = db.Column(db.String(300), nullable = False)
    Description = db.Column(db.String(3000), nullable = True)
    #optional fields
    keywords = db.Column(db.String(300))
    # target_workers = db.Column(db.Integer)
    fix_price = db.Column(db.Float)
    time_limit = db.Column(db.Integer)

    #Important fields
    #--------------------------------------------------------
    # waiting_time_window = db.Column(db.Integer) # in minutes
    min_active = db.Column(db.Integer)
    min_waiting = db.Column(db.Integer)
    max_active = db.Column(db.Integer)
    max_waiting = db.Column(db.Integer)
    #--------------------------------------------------------

    #this will not be populated from admin
    hit_expiry = db.Column(db.Integer, default = 60*60*24*7) #one week
    autopay_delay = db.Column(db.Integer, default = 60*60*72) # three days


    #Qualifications
    country = db.Column(db.String(100))
    approval_rate = db.Column(db.Integer)
    number_of_HITS = db.Column(db.Integer)


    task_url = db.Column(db.String(500), nullable = False)

    date_created = db.Column(db.DateTime, default = datetime.datetime.utcnow())

    def __init__(self, p_id, task_status, title, Description, keywords, fix_price, time_limit, country, approval_rate, number_of_HITS, task_url,
                 min_active, min_waiting, max_active, max_waiting, date_created):
            self.p_id = p_id
            # self.HIT_id = HIT_id
            self.task_status = task_status
            self.title = title
            self.Description = Description
            self.keywords = keywords
            self.fix_price = fix_price
            self.time_limit = time_limit
            self.country = country
            self.approval_rate = approval_rate
            self.number_of_HITS = number_of_HITS
            self.task_url = task_url
            self.min_active = min_active
            self.min_waiting = min_waiting
            self.max_active = max_active
            self.max_waiting = max_waiting
            self.date_created = date_created



    def __repr__(self):
        return 'Task name'.format(self.title)


######################## END ###################################
