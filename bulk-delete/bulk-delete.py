#!/usr/bin/env python3

import sys
import argparse
import requests
import json
from ratelimit import limits, sleep_and_retry

# Command line argument parsing
parser = argparse.ArgumentParser()
parser.add_argument("-x", "--quiet", help = "reduces output verbosity", action = "store_false")
parser.add_argument("-e", "--environment", help = "<REQUIRED> the ID of the environment in which the users you wish to delete are stored", required = True)
parser.add_argument("-c", "--client", help = "<REQUIRED> the ID of an app configured with the ability to delete users", required = True)
parser.add_argument("-s", "--secret", help = "<REQUIRED> the corresponding secret of an app configured with the ability to delete users", required = True)
parser.add_argument("-p", "--population", help = "the ID of the population in which the users you wish to delete are stored")
parser.add_argument("-q", "--query", nargs="+", help = "a SCIM 2.0 filter")
parser.add_argument("-w", "--skip", nargs="+", help = "user IDs to be skipped during deletion")
args = parser.parse_args()

ENVIRONMENT_ID = args.environment
CLIENT_ID = args.client
CLIENT_SECRET = args.secret
POPULATION_ID = args.population
SKIP_USER_IDS_ARRAY = args.skip
QUERY = ""

if POPULATION_ID:
    QUERY = "(population.id eq \"{}\")".format(POPULATION_ID)

if POPULATION_ID and args.query:
    QUERY = QUERY + " and (" + " ".join(args.query) + ")"
elif args.query:
    QUERY = " ".join(args.query)

if SKIP_USER_IDS_ARRAY:
    SKIP_USER_IDS = set(SKIP_USER_IDS_ARRAY)
else:
    SKIP_USER_IDS = []

VERBOSE = args.quiet
MAX_ATTEMPTS = 3

# Log failures
def log_error(description, r):
    print("[ERROR] " + description + " ({}):".format(str(r.status_code)))
    print("[ERROR] Request: " + r.request.url)
    if r.request.body:
        print("[ERROR] " + r.request.body)
    print("[ERROR] " + r.text)

# Constructs the users URL with the given query, if any
def build_query_url():
    global QUERY
    url = "https://api.pingone.com/v1/environments/{}/users".format(ENVIRONMENT_ID)
    if QUERY:
        url += "?filter={}".format(QUERY)
    return url

# Request a token with client credentials
def get_token():
    global token, BEARER_HEADER
    token_url = "https://auth.pingone.com/{}/as/token?grant_type=client_credentials&scope=p1:read:env:user p1:delete:env:user".format(ENVIRONMENT_ID)

    try:
        r = requests.post(
            token_url,
            headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
            auth = (CLIENT_ID, CLIENT_SECRET))
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_error("Error requesting access token", r)
        sys.exit()

    token = r.json()["access_token"]
    BEARER_HEADER = {"Authorization": "Bearer {}".format(token)}

# Fetches all users on current page then deletes them
# If there is a next page, fetch it and continue deletion
@sleep_and_retry
@limits(calls = 95, period = 1)
def delete_page(page):
    users = []
    index = 1
    while True:
        # Delete users on current page
        for user in page["_embedded"]["users"]:
            if not user["id"] in SKIP_USER_IDS:
                delete_user(user)

        # If there's a next page link, follow it
        if "next" in page["_links"]:
            # Parse and follow the next link from response
            link = page["_links"]["next"]["href"]
            try:
                if VERBOSE:
                    print("Fetching next page... ({})".format(str(index)))
                r = requests.get(link, headers = BEARER_HEADER)
                r.raise_for_status()
                index += 1
            except requests.exceptions.HTTPError as e:
                log_error("Error fetching users", r)

            page = r.json()
        else:
            break

# Delete a user
@sleep_and_retry
@limits(calls = 95, period = 1)
def delete_user(user):
    user_id = user["id"]
    delete_url = "https://api.pingone.com/v1/environments/{}/users/{}".format(ENVIRONMENT_ID, user_id)

    attempt = 1
    while (attempt <= MAX_ATTEMPTS):
        try:
            r = requests.delete(delete_url, headers = BEARER_HEADER)
            r.raise_for_status()
            if VERBOSE:
                print("Deleting {} ({})".format(user["username"], user_id))
            break
        except requests.exceptions.HTTPError as e:
            # If the status code is 401, refresh token and retry
            if e.response.status_code == 401:
                if VERBOSE:
                    print("Refreshing token...")
                get_token()
            else:
                log_error("Error deleting user {}".format(user_id), r)
        if VERBOSE:
            print("Retrying... attempt {}/{}".format(attempt, MAX_ATTEMPTS))
        attempt += 1

# Main
get_token()

users_url = build_query_url()
attempt = 1
while (attempt <= MAX_ATTEMPTS):
    try:
        r = requests.get(users_url, headers = BEARER_HEADER)
        r.raise_for_status()
        msg = "{} user(s) found in environment {}".format(str(r.json()["count"]), ENVIRONMENT_ID)
        if QUERY:
            msg += " matching {}".format(QUERY)
        print(msg)
        delete_page(r.json())
        break
    except requests.exceptions.HTTPError as e:
        # If the status code is 401, refresh token and retry
        if e.response.status_code == 401:
            if VERBOSE:
                print("Refreshing token...")
            get_token()
        else:
            log_error("Error fetching users", r)
    if VERBOSE:
        print("Retrying... attempt {}/{}".format(attempt, MAX_ATTEMPTS))
    attempt += 1

print("Done")