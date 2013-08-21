Kudos
=====

Hackbright final project - employee recognition web app


Overview
=====
This is a webapp designed to use internally at your company. It provides a central place for employees to post recognition for other employee's work, whereas it might go unnoticed otherwise. You have a main feed where all posts are displayed and then clicking on either a team or specific person will show more information, as well as any posts they have been tagged in. A great way for new employees to see what everyone has been working on.


Getting the Data (get_hackbright_data.py)
=====
The app is currently running with information for Hackbright students and instructors. Get_hackbright_data.py takes my file with Hackbright user info, turns it into a JSON object, and imports the data into my database. This populates three tables: users, teams, and users_teams. 


Databases (models.py)
=====
The SQLite database includes 6 tables to store information for users, teams, and data related to created posts. SQLAlchemy is used as the ORM to map the tables their respective classes in models.py. 


