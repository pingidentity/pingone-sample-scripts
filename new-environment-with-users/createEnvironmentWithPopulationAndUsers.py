#!/usr/bin/env python3
# 
#
# This script uses the requests module of python to make calls to P14C to create a new environment with some sample users in a population.
# 
# All you need are:
# 1.) Organization ID
# 2.) Environment ID (the original environment, not the one you'll create)
# 3.) Client ID for the app you'll use to set up a new environment.
# 4.) Client Secret
# 5.) Have your app set up for Client Credentials grant type and Client Secret Post (not Client Secret Basic)
# 
# 
# To run, fill in information 1-4 in the variables just below and run:
#   python createNewEnvWithUsers.py
# If successful, the terminal output should look like the following.
#   Access token successfully retrieved.
#   New environment created: Environment-03/27/19-10.49.59.790148
#   New population created: Population_03/27/19-10.50.00.122141
#   10 users created
#
#
# 
import requests
import json
from datetime import datetime

# Enter this information from your application that you'll be using to create the new environment and add users.
ORGANIZATION_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
ENVIRONMENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
CLIENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
CLIENT_SECRET='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
# Environment ID where the admin user is.
ADMIN_ENVIRONMENT_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
# The Admin user is for looking at the users created from this script.
ADMIN_USER_ID='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
# Number of sample users to create
USERS = 10



#
# Get Access Token
#
url = 'https://auth.pingone.com/' + ENVIRONMENT_ID + '/as/token'
# Body
payload = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}
# Headers
headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}
# POST
try:
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("Couldn't retrieve the access token.")
    print(response.request.headers)
    print(response.request.body)
    print(response.text)
    print(err)
    raise
else:
    response_json = response.json()
    access_token = response_json["access_token"]
    print("Access token successfully retrieved.")


#
# Create new environment.
#
url = 'https://api.pingone.com/v1/organizations/' + \
    ORGANIZATION_ID + '/environments'
now = datetime.now()
timestamp = now.strftime("%x-%H.%M.%S.%f")
name = "Environment-" + timestamp
description = "New environment from script"
# Body
payload = {
    "name": name,
    "region": "NA",
    "type": "SANDBOX",
    "description": description
}
# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + access_token
}
# POST
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print("Couldn't create a new environment due to an exception.")
    print(response.request.headers)
    print(response.request.body)
    print(response.text)
    print(err)
    raise
else:
    response_json = response.json()
    new_environment_id = response_json["id"]
    print("New environment created: " + name)


#
# Create a new population.
#
url = 'https://api.pingone.com/v1/environments/' + new_environment_id + '/populations'
# Time for use as unique identifier.
now = datetime.now()
timestamp = now.strftime("%x-%H.%M.%S.%f")
name = "Population_" + timestamp
description = "New population from script"
# Body
payload = {
    "name": "Population_" + timestamp,
    "description": "New population from script."
}
# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + access_token
}

# POST
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(response.request.headers)
    print(response.request.body)
    print(response.text)
    print(err)
    raise
else:
    response_json = response.json()
    population_id = response_json["id"]
    print("New population created: " + name)


#
# Add identity data admin role for the new population to admin user
#
url = 'https://api.pingone.com/v1/environments/' + ADMIN_ENVIRONMENT_ID + '/users/' + ADMIN_USER_ID + '/roleAssignments'
# Body
payload = {
    "role": {
        "id": "0bd9c966-7664-4ac1-b059-0ff9293908e2"
    },
    "scope": {
        "id": new_environment_id,
        "type": "ENVIRONMENT"
    },
    "#scope": {
        "id": population_id,
        "type": "POPULATION"
    }
}
# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + access_token
}

# POST
try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    response.raise_for_status()
except requests.exceptions.HTTPError as err:
    print(response.request.headers)
    print(response.request.body)
    print(response.text)
    print(err)
    raise
else:
    response_json = response.json()
    print("Identity Data Admin added to admin user (id:" + ADMIN_USER_ID + ").")



#
# Create some users.
#
url = 'https://api.pingone.com/v1/environments/' + new_environment_id + '/users'
# Loop to create the users.
for i in range(USERS):
    username = "user." + str(i)
    email = username + "@email.com"
    # Body
    payload = {
        "username": username,
        "email": email,
        "name": {
            "given": username
        },
        "population": {
            "id": population_id
        },
        "password": {
            "value": "change_Password1"
        }
    }
    # Headers
    headers = {
        "Content-Type": "application/vnd.pingidentity.user.import+json",
        "Authorization": "Bearer " + access_token
    }

    # POST
    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print("***Couldn't create the users due to an exception.***")
        print(response.request.headers)
        print(response.request.body)
        print(response.text)
        print(err)
        raise
    else:
        response_json = response.json()
print(str(USERS) + " users created")

