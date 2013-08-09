#!flask/bin/python

import json
import urllib2

from flask.ext.sqlalchemy import SQLAlchemy 
from flask import session 

import app
from app.models import User, Post, UserTeam, Team

db = app.db

ABOUT_PAGE_JSON_URL = "http://about.corp.dropbox.com/?output=json"

def create_user(first_name, last_name, nickname, email, list_of_teams, mobile, photo, bio, username):
    # You'd remove the rest of this method and add the user to your database here

    #When readding data - check to see if user already exists based on email. If yes, update columns, if no, insert new_user

    #for each user, iterate through list of teams and create entries in users_teams
    print email,
    if not email:
        return


    new_user=User(
        photo=photo,
        firstname = first_name,
        lastname = last_name,
        nickname = nickname,
        email = email, 
        phone = mobile,
        about_me = bio,
        username = username,
        )


    db.session.add(new_user) 
    db.session.commit()

    user_id = new_user.id

    for team in list_of_teams:
        new_users_teams=UserTeam(
            user_id=user_id,
            team_id=team,
            )
        db.session.add(new_users_teams)
        db.session.commit()

    #if len(list_of_teams) == 0:
    #    print "%s %s has no teams" % (first_name, last_name)
    #elif len(list_of_teams) == 1:
    #    print "%s %s with email %s is a member of 'Team %s'" % (first_name, last_name, email, list_of_teams[0])
    #elif len(list_of_teams) > 1:
    #    team_names_prepended_with_team = ("'Team %s'" % team for team in list_of_teams)
    #    team_names = ', '.join(team_names_prepended_with_team)
    #    print "%s %s with email %s is a member of the following teams:%s" % (first_name, last_name, email, team_names)
    #else:
    #    assert False, "Should never get here"

def create_teams(all_teams):
    teams = all_teams.keys()
    for team in teams:
        new_team=Team(teamname=team)
        db.session.add(new_team)
        db.session.commit()

def main():
    raw_data = urllib2.urlopen(ABOUT_PAGE_JSON_URL)
    users = json.load(raw_data)['users']

    print "Creating users with emails:",

    all_teams = {}
    for user in users:
        # Below we use the user['r_first_name'] property. There's also a user['first_name']
        # field which is what the user said is his/her first name. But this is bogus for
        # lots of employees.
        user_real_first_name = user['r_first_name']
        user_real_last_name = user['r_last_name']
        user_nickname = user['nickname']
        user_email = user['email']
        user_list_of_teams = user['teams']
        user_mobile_phone = user['mobile_phone']
        user_photo = user['picture']
        user_bio = user['bio']
        username = user['username']

        for team in user_list_of_teams:
            if team not in all_teams:
                all_teams[team] = 1

        create_user(
            user_real_first_name,
            user_real_last_name,
            user_nickname,
            user_email,
            user_list_of_teams,
            user_mobile_phone, 
            user_photo,
            user_bio,
            username,
        )

    create_user(
        "melissa", 
        "skevington",
        "missy",
        "melissaskevington@gmail.com",
        ["kudos"],
        "5182655596",
        "http://about/media/badges/abhishek.thumb.jpg",
        "hi", 
        "mskeving",
        )
    create_teams(all_teams)

    print "Done."

#add this so when it's imported, does not run. 
if __name__ == '__main__':
    main()
