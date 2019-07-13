from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField, FloatField, SelectField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired


class CreateNewProject(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    Description = StringField('Description', validators=[DataRequired()])

    create_button = SubmitField('Create')

class EditProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    Description = StringField('Description', validators=[DataRequired()])

    submit = SubmitField('Update')



class CreateNewTask(FlaskForm):
    hit_title = StringField('HIT Title', validators=[DataRequired()])
    hit_desc = StringField('Description', widget=TextArea(), validators=[DataRequired()])

    keywords = StringField('keywords', validators=[DataRequired()], default='survey, feedback, robot control')
    # target_workers = IntegerField('Target Workers', validators=[DataRequired()])
    fix_price = FloatField('Fix Price (USD)')
    time_limit = IntegerField('Time limit (in minutes)', validators=[DataRequired()])

    country = StringField('Country', validators=[DataRequired()], default="US")
    percent_approved = IntegerField('Percent Approved', validators=[DataRequired()], default=97)
    HITS_approved = IntegerField('# of HITS Approved', validators=[DataRequired()], default=1000)


    task_url = StringField('URL for TASK', validators=[DataRequired()], default = 'https://pepperanywhere.herokuapp.com/task')

    min_active = IntegerField('Min. Number of Active Workers', validators=[DataRequired()], default=2)
    min_waiting = IntegerField('Min. Number of Waiting Workers', validators=[DataRequired()], default=1)
    max_active = IntegerField('Max. Number of Active Workers', validators=[DataRequired()], default=3)
    max_waiting = IntegerField('Max. Number of waiting Workers', validators=[DataRequired()], default=3)


    submit = SubmitField('Create a New Task')


class EditTask(FlaskForm):
    hit_title = StringField('HIT Title', validators=[DataRequired()])
    hit_desc = StringField('Description', widget=TextArea(), validators=[DataRequired()])
    keywords = StringField('keywords', validators=[DataRequired()], default='survey, feedback, robot control')
    # target_workers = IntegerField('Target Workers', validators=[DataRequired()])
    fix_price = FloatField('Fix Price (USD)', validators=[DataRequired()], default=1.0)
    time_limit = IntegerField('Time limit (in minutes)', validators=[DataRequired()])

    country = StringField('Country', validators=[DataRequired()], default="US")
    percent_approved = IntegerField('Percent Approved', validators=[DataRequired()], default=97)
    HITS_approved = IntegerField('# of HITS Approved', validators=[DataRequired()], default=1000)

    task_url = StringField('URL for TASK', validators=[DataRequired()], default = 'https://pepperanywhere.herokuapp.com/task')

    min_active = IntegerField('Min. Number of Active Workers', validators=[DataRequired()], default=2)
    min_waiting = IntegerField('Min. Number of Waiting Workers', validators=[DataRequired()], default=1)
    max_active = IntegerField('Max. Number of Active Workers', validators=[DataRequired()], default=3)
    max_waiting = IntegerField('Max. Number of waiting Workers', validators=[DataRequired()], default=3)


    submit = SubmitField('Save Changes')

class MigrateWorkers(FlaskForm):
    NumberOfWorkers = IntegerField('Number of Workers to Migrate', validators=[DataRequired()], default=2)
    submit = SubmitField('Migrate')
