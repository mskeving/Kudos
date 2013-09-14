# Kudos

Hackbright final project

This is a webapp designed to use internally at your company. It provides a central place for employees to post recognition for other employee's work, whereas it might go unnoticed otherwise. You have a main feed where all posts are displayed and then clicking on either a team or specific person will show more information, as well as any posts they have been tagged in. A great way for new employees to see what everyone has been working on.

## Overview

This is a Python webapp using a Flask framework. The data is stored in SQLite using SQLAlchemy as the ORM. The front end is done with JavaScript using jQuery, HTML, and custom CSS. 

## Views

[Home page](https://dl-web.dropbox.com/spa/b0x9nvfo1ovrbum/myvl10w5.png) to view all posts. Optimized to turn mobile some day

Individual [user pages](https://dl-web.dropbox.com/spa/b0x9nvfo1ovrbum/4zuqt1-z.png) to see contact information and all kudos sent to that user

[Team pages](https://dl-web.dropbox.com/spa/b0x9nvfo1ovrbum/myvtv4kk.png) to view everyone on each team. The bottom of the page will display kudos that team has been tagged in.  

## Setup on your machine

1. Clone the repo locally

2. Create virtual env
	```
	$ pip install virtualenv
	$ virtualenv env
	$ source env/bin/activate
	```

2. install requirements from requirements.txt
	```
	$ pip install -r requrements.txt
	```

3. Create database: 
	```
	$ python db_create.py
	```

4. Edit db to include your necessary info to login and view index.html. NOTE: must use your actual email
	```
	$ sqlite3 app.db
	> inset into users default values;
	> update users set email="YOU@EMAIL.COM", firstname="FIRSTNAME", lastname="LASTNAME", username="USERNAME"  where id = 1;
	```

5. Start your web server
	```
	python run.py
	```


This is bare minimum to get site running. No avatars will be shown, you will be the only option for tagging, and there will be no user/team relationships. You can add more users/teams to the database manually for more options. The database schema can be found in models.py. 

