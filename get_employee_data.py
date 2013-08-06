#!/usr/bin/python

import json
import urllib2

ABOUT_PAGE_JSON_URL = "http://about.corp.dropbox.com/?output=json"

def create_user(first_name, last_name, email, list_of_teams):
    # You'd remove the rest of this method and add the user to your database here

    if len(list_of_teams) == 0:
        print "%s %s has no teams" % (first_name, last_name)
    elif len(list_of_teams) == 1:
        print "%s %s with email %s is a member of 'Team %s'" % (first_name, last_name, email, list_of_teams[0])
    elif len(list_of_teams) > 1:
        team_names_prepended_with_team = ("'Team %s'" % team for team in list_of_teams)
        team_names = ', '.join(team_names_prepended_with_team)
        print "%s %s with email %s is a member of the following teams:%s" % (first_name, last_name, email, team_names)
    else:
        assert False, "Should never get here"

def main():
    print "Fetching data..."
    raw_data = urllib2.urlopen(ABOUT_PAGE_JSON_URL)
    users = json.load(raw_data)['users']

    print "Populating thumbs for %s users..." % len(users)
    for user in users:
        # Below we use the user['r_first_name'] property. There's also a user['first_name']
        # field which is what the user said is his/her first name. But this is bogus for
        # lots of employees.
        user_real_first_name = user['r_first_name']
        user_real_last_name = user['r_last_name']
        user_email = user['email']
        user_list_of_teams = user['teams']

        create_user(
            user_real_first_name,
            user_real_last_name,
            user_email,
            user_list_of_teams,
        )

    print "Done."

if __name__ == '__main__':
    main()
