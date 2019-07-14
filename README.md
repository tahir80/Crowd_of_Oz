# Crowd of Oz
This repository contains the implementation of Crowd of Oz (CoZ) -- a crowd powered conversational assistant for the Pepper robot. CoZ helps to recruits crowd-workers as tele-operators to control the social behaviors of the robot. CoZ achieves this by providing media rich interfaces to assist crowd-workers to contextualize the conversation and defining pavilion algorithm to sustain crowd workers by analyzing turnover conditions, e.g. when workers return, submit and abandon our task.
## System Diagram

![OverviewDiagram1](https://user-images.githubusercontent.com/7135544/61186487-40781f80-a666-11e9-9394-685daccaaae9.jpg)

**You can find the Media Manager from App folder and Communication adaptor is located in the root folder. Crowd_control is also located in the app folder**

## Pavilion Algorithm
The Pavilion algorithm handles asynchronous arrival/departure of crowd workers from MTurk.com in the waiting and active queue for enabling real-time crowdsourcing (RTC)
### Introduction
Pavilion tries to retain workers in the active queue -- a queue which contains workers who are engaged with the task-- in addition to waiting queue based on turnover conditions (e.g. when workers leave the task either from the waiting or active queue). A worker can leave the task either when she submits a task, returns it, or abandons it.
Following conditions are handled in Pavilion:
1) When worker leaves from waiting queue by submitting Human Intelligence Task (HIT) --> Pavilion hires a new worker
2) When worker leaves from the active queue by submitting HIT --> **a)** Pavilion moves worker from waiting to active queue, **b)** Pavilion hires a new worker to fullfil the deficiency in the waiting queue
3) When worker leaves from the active queue by returning HIT --> Pavilion moves worker from waiting to the active queue
4) When worker leaves from the waiting queue by returning HIT --> NONE

## Admin Controls
In addition to managing workers in the active and waiting queue, we have also provided basic admin controls for;
1. Creating a new project
2. Creating a HIT/task on Amazon Mechanical Turk (MTurk)
3. Stopping a current job manually --> this will auto-submit HITs from all workers
4. Expiring a HIT 
5. Migrating workers manually if needed from waiting to active queue
## Local Installation
First install all dependencies in requirements.txt file and then Uncomment the following code from run.py containing in the root folder. Make sure that ***create_app*** contains 'dev' as an argument. For production settings, change this to 'prod'
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

## Installation on Heroku
1. clone our project and set it up in local git repository.
2. Sign up for Heroku
3. download and install Heroku CLI
4. create an app first, give it a unique name
5. then create a database --> click on resources tab under your newly created app --> search postgres --> and add hobby-dev (it's free)
6. click on your database name -->click on settings -->credentials --> you can copy the URI to the prod.py file but its NOT RECOMMENDED, you don't need to do anything. Everything is setup in prod.py under config folder.
7. now come back to console and type: heroku login
8. go back to app, and click on deploy and then run the following commands(you must be in the root folder of your project)
```
git add .
git commit -am "make it better"
git push heroku master
```
9. you can open the website using heroku open or use provided url after successful installtion

