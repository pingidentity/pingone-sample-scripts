from subprocess import call
import sys
call( ["node", "/Applications/Splunk/bin/scripts/poll_activities.js"] + sys.argv )