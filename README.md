[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![Flask-SocketIO](https://img.shields.io/badge/Flask--socketIO-1.0.2-red.svg)](https://flask-socketio.readthedocs.io/en/latest/)
[![Python](https://img.shields.io/badge/Python-3.7-blue.svg)](https://www.python.org/downloads/)
[![boto3](https://img.shields.io/badge/Boto3-1.9.42-orange.svg)](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html)
[![openTOK](https://img.shields.io/badge/OpenTok-WebRTC-brightgreen.svg)](https://tokbox.com/)



# Crowd of Oz
This repository contains the implementation of Crowd of Oz (CoZ) — a crowd-powered conversational assistant for the Pepper robot. CoZ helps to recruit crowd workers as teleoperators to control the speech of the robot. CoZ achieves this by providing media-rich interfaces to assist crowd workers in contextualizing the conversation and defining a pavilion algorithm to sustain crowd workers by analyzing turnover conditions, such as when workers return, submit, and abandon our task.
## System Diagram

![system_diagram](https://user-images.githubusercontent.com/7135544/61368091-67fd0100-a88d-11e9-8428-042ed0ec0fec.png)

To learn more about the system diagram, please refer to this paper: https://www.sciencedirect.com/science/article/pii/S2352711019302699

## How does it work?
1. Create a new project by opening the create_project page
2. After creating the project, you will see a link ***Create New Task*** on the home page. Click this link to create a new task or HIT.
3. After that, click on the ***See Tasks*** from the home page.
4. You will see the option ***Make it Live***. Click it to post the job to Amazon Mechanical Turk. Do not forget to replace the values of OpenTOK, IBM Watson (if you want to use Speech to text on crowd interfaces), and Amazon Mechanical Turk Settings in the ```__init__``` file from the root folder
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
  * For openTOK visit here: https://tokbox.com/
  * For IBM Watson Speech to text visit here: https://www.ibm.com/watson/services/speech-to-text/
  * For Amazon Mechanical Turk settings and Boto3 framework visit here: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/mturk.html

5. First, you need to run all scripts on a Windows/Mac or Linux-based PC. This PC will act as a middleware between your robot and flask-based web server as shown in the diagram.
6. Please provide the IP address of the robot where asked.
7. For the Google speech-to-text script located in the Crowd-of-Oz\Communication_adaptor\Google_Speech_to_text, you need to provide your credentials in the Google.py file. To run the Google speech-to-text service, please run the module_speechrecognition.py. Give credit and thanks to: https://github.com/JBramauer/pepperspeechrecognition
8. In the OOCSI folder located at Crowd-of-Oz\Communication_adaptor\OOCSI, please run the main.py. Give credit and thanks to: https://github.com/iddi/oocsi-python
9. From the SocketIO client, please run the socket_IO_bridge.html and leave it open in the browser.
10. If you have already deployed your web application as explained in the section: ***Installation on Heroku***, then please install chrome or firefox browser extension to run the audio and video publishers. The instructions on how to install the browser extension are available here: https://github.com/opentok/screensharing-extensions. 
11. Also install and run the Choregraph (based on the operating system) and make sure that it is running. For installation of Choregraph, follow this link: http://doc.aldebaran.com/2-4/dev/community_software.html. Also, make sure that the camera view is displayed on the main interface of the Choregraph. You need to broadcast a camera view from the Choregraph application to the crowd workers.
12. After that, open web pages ***publish_video*** and ***publish_audio***. For publishing video click on the ***Share your screen*** and select Choregraph's application camera view.
13. At the end of the conversational task, you have to manually click the STOP button from the ***see tasks*** link. This operation will make sure that HIT from all crowd workers is submitted automatically. Please inform your potential workers beforehand in the instructions. After a few seconds, do not forget to click on the ***Expire HIT***. This operation will make sure that no other new workers accept this HIT.
14. Finally, review and pay the crowd workers.
15. Do not forget to stop all scripts including audio and video publishers running on the Middleware.

***Note: The main logic of CoZ is located in app --> Crowd_control --> events.py***. please also see the static --> js folder for client-side logic. 


## Pavilion Algorithm
The Pavilion algorithm handles the asynchronous arrival/departure of crowd workers from MTurk.com in the waiting and active queue for enabling real-time crowdsourcing (RTC)
### Introduction
Pavilion tries to retain workers in the active queue -- a queue that contains workers who are engaged with the task-- in addition to the waiting queue based on turnover conditions (e.g. when workers leave the task either from the waiting or active queue). A worker can leave the task either when she submits a task, returns it, or abandons it.
The following conditions are handled in Pavilion:
1) When a worker leaves from waiting queue by submitting Human Intelligence Task (HIT) --> Pavilion hires a new worker
2) When a worker leaves the active queue by submitting HIT --> **a)** Pavilion moves the worker from waiting to active queue, **b)** Pavilion hires a new worker to fulfill the deficiency in the waiting queue
3) When worker leaves the active queue by returning HIT --> Pavilion moves the worker from waiting to the active queue
4) When worker leaves the waiting queue by returning HIT --> NONE

## Local Installation
First, install all dependencies in the requirements.txt file and then uncomment the following code from run.py contained in the root folder. Make sure that ***create_app*** contains 'dev' as an argument. For production settings, change this to 'prod'
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
   * You first need to log in using default login credentials (user name: harry@potters.com, Password: secret)
2. To create a new project: http://127.0.0.1:5000/create_project
3. See the waiting sample page: http://127.0.0.1:5000/waiting_room and the main task sample page: http://127.0.0.1:5000/main_task

## Installation on Heroku
1. Clone our project and set it up in the local git repository.
2. Sign up for Heroku: https://signup.heroku.com/identity
3. Download and install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli#download-and-install
4. Create an app first, and give it a unique name: https://dashboard.heroku.com
5. Then create a database --> click on the resources tab under your newly created app --> search postgres --> and add hobby-dev (it's free)
6. Click on your database name -->click on settings -->credentials --> you can copy the URI to the prod.py file but it's NOT RECOMMENDED, you don't need to do anything. Everything is set up in prod.py under the config folder.
7. Now come back to the console and type: ```heroku login```
8. Go back to the app, click on deploy and then run the following commands(you must be in the root folder of your project)
```
git add .
git commit -am "make it better"
git push heroku master
```
9. You can open the website using Heroku open or use provided URL after successful installation

## AMAZON S3 storage
1. log in to the AWS console (https://aws.amazon.com/console/)
2. Select Amazon S3 from the storage
3. Click on create a new bucket
4. In the name and region section, give your bucket a unique name and select the appropriate region. Click next
5. Leave the configure options as default. Click next
6. In the set permissions section, under ***Manage System permissions*** select Grant Amazon S3 Log Delivery group write access to this bucket
7. When you click on the bucket name, it will lead you to a page where you can add files
8. Upload **"local_db.backup"** --> it is inside the root folder
9. Click on the uploaded file --> copy the link and go to the console again
10. Type this: heroku pg:backups:restore "YOUR COPIED LINK"
11. Once done, restart the service using: heroku restart

### Simplified ERD Model
<img width="791" alt="ERD_Model" src="https://user-images.githubusercontent.com/7135544/61370381-916c5b80-a892-11e9-8964-befe49c5409f.png">

## License
This code pattern is licensed under the MIT License. Separate third-party code objects invoked within this code pattern are licensed by their respective providers according to their separate licenses.
