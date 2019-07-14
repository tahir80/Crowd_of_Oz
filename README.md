# Crowd of Oz
This repository contains the implementation of Crowd of Oz (CoZ) -- a crowd powered conversational assistant for the Pepper robot. CoZ helps to recruits crowd-workers as tele-operators to control the social behaviors of the robot. CoZ achieves this by providing media rich interfaces to assist crowd-workers to contextualize the conversation and defining pavilion algorithm to sustain crowd workers by analyzing turnover conditions, e.g. when workers return, submit and abandon our task.

[[https://github.com/tahir80/Crowd-0f-Oz/master/OverviewDiagram1.jpg]]
# Local Installation
Uncomment the following code from run.py containing in the root folder. Make sure that ***create_app*** contains 'dev' as an argument. For production settings, change this to 'prod'
```python
#--------local testing----------------
if __name__ == "__main__":
    flask_app = create_app('dev')
    with flask_app.app_context():
        db.create_all()
    flask_app.run()
#------------------------------------------
```
Then simply type: ```python run.py ```

1. To register yourself as Admin: http://127.0.0.1:5000/register
   * You first need to login using default login credentials (user name: harry@potters.com, Password: secret)
2. To create a new project: http://127.0.0.1:5000/create_project
3. See waiting sample page: http://127.0.0.1:5000/waiting_room
4. See main task sample page: http://127.0.0.1:5000/main_task
