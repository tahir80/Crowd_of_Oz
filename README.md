[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)


# Crowd of Oz
This repository contains the implementation of Crowd of Oz (CoZ) -- a crowd powered conversational assistant for the Pepper robot. CoZ helps to recruits crowd-workers as tele-operators to control the social behaviors of the robot. CoZ achieves this by providing media rich interfaces to assist crowd-workers to contextualize the conversation and defining pavilion algorithm to sustain crowd workers by analyzing turnover conditions, e.g. when workers return, submit and abandon our task.
## System Diagram

![OverviewDiagram1](https://user-images.githubusercontent.com/7135544/61186487-40781f80-a666-11e9-9394-685daccaaae9.jpg)

**You can find the Media Manager from App folder and Communication adaptor is located in the root folder. Crowd_control is also located in the app folder**

## How it Works?
1. create a new project by opening the create_project page
2. After creating a project, you will see a link ***Create New Task*** on the home page. Click this link to create a new task or HIT.
3. After that, click on the ***See Tasks*** from the home page and click it.
4. You will see the option ***Make it Live***. Click it to post the job to Amazon Mechanical Turk. Do not forget to replace the values of OpenTOK, IBM Watson (if you want to use Speech to text on crowd interfaces) and Amazon Mechanical Turk Settings from ```__init__``` file from the root folder
  * For openTOK visit here: https://tokbox.com/
  * For IBM watson Speech to text visit here: https://www.ibm.com/watson/services/speech-to-text/
  * For Amazon Mechanical Turk settings and Boto3 framework visit here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html

```python
############OPENTOK credentials#########################
OPENTOK_API_KEY = 'YOUR_OWN_API_KEY'
OPENTOK_SESSION_ID = 'YOUR_OWN_SESSION_ID'
OPENTOK_TOKEN_ID = 'YOUR_OWN_TOKEN_ID'
##########################################################


############IBM watson credentials#########################
STT_USERNAME = "YOUR_OWN_STT_USERNAME"
STT_PASSWORD = "YOUR OWN_STT_PASSWORD"
STT_APIKEY = "YOUR_OWN_STT_APIKEY"
STT_URL = "YOUR_OWN_STT_URL"
##########################################################


##########Amazon Mechanical Turk Settings################################
AWS_ACCESS_KEY_ID = "YOUR_OWN_AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "YOUR_OWN_AWS_SECRET_ACCESS_KEY"

```


5. First, you need to run all scripts in a Windows/Mac or linux based PC. This PC will act as a middleware betwen your robot and flask based web server as shown in the diagram.
6. Please provide the IP address of the robot where asked.
7. For Google speech to text script located in Crowd-of-Oz\Communication_adaptor\Google_Speech_to_text, you need to provide your own credentials in the Google.py file. To run the Google speech to text service, please run module_speechrecognition.py.
8. In the OOCSI folder located at Crowd-of-Oz\Communication_adaptor\OOCSI, please run the main.py
9. From SocketIO client, please run the socket_IO_bridge.html and leave it open in the browser.
10. If you have already deployed your web application as explained the section: ***Installation on Heroku***, then please intall chrome or firefox browser extension in order to run the audio and video publishers. The instructions on how to install the browser extension is available here: https://github.com/opentok/screensharing-extensions. After that, open web pages ***publish_video*** and ***publish_audio***. For publishing video click on the ***Share your screen***.


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

## AMAZON S3 storage
1. login to AWS console (https://aws.amazon.com/console/)
2. select Amazon S3 from storage
3. click on create new bucket
4. In the name and region section, give your bucket a unique name and select the appropriate region.Click next
5. Leave the configure options as default. Click next
6. In the set permissions section, under ***Manage System permissions*** select Grant Amazon S3 Log Delivery group write access to this bucket
7. when you click on the bucket name, it will lead you to a page where you can add files
8. upload **"local_db.backup"** --> it is inside the root folder
9. click on the uploaded file --> copy the link and go to console again
10. type this: heroku pg:backups:restore "YOUR COPIED LINK"
11. once done, restart the service using : heroku restart

### Database Model

