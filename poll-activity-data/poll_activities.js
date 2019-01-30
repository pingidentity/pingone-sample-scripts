const rp = require('request-promise'),
      moment = require('moment-timezone'),
      fs = require('fs');

const STATUS_FILE = "/Applications/Splunk/bin/scripts/status.json";
const ENV_ID = "your-env-id";
const CLIENT_ID = "your-client-id";
const CLIENT_SECRET = "your-client-secret";
const tokenAuthRequestOptions = {
    method: 'POST',
    uri: `https://auth.pingone.com/${ENV_ID}/as/token`,
    port: 443,
    headers: {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded'
    },
    form: {
        grant_type: 'client_credentials',
        scope: 'p1:read:env:activity',
        client_id: `${CLIENT_ID}`,
        client_secret: `${CLIENT_SECRET}`
    },
    json: true
};

const activitiesRequestOptions = (accessToken, accessTokenType, range) => {
    var json = {
        method: 'GET',
        uri: `https://api.pingone.com/v1/environments/${ENV_ID}/activities?filter=createdat%20ge%20%22{lowerbound}%22%20and%20createdat%20le%20%22{upperbound}%22&limit=500`,
        port: 443,
        headers: {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': `${accessTokenType} ${accessToken}`
        },
        json: true,
        forever: true
    };
    if (!range) {
        range = [moment().tz('utc').subtract(5, 'minutes').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z', moment().tz('utc').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z'];
    }
    json.uri = json.uri.replace("{lowerbound}", range[0])
                       .replace("{upperbound}", range[1]);
    return json;
};

// given a range, get all activities for that range
const getAllActivities = async (range) => {
    var options;
    let done = false;
    var token = null;
    var count = 0;
    let startApp = new Date();
    while (!done) {
        let start = new Date();
        if (!token) {
            try {
                // get the token response
                token = await rp(tokenAuthRequestOptions);

                let uri = (options) ? options.uri : null;
                options = activitiesRequestOptions(token.access_token, token.token_type, range);
                if (uri) options.uri = uri;
            } catch (err) {
                // this shouldn't happen but life is unpredictable, so quit the loop if it does.
                console.error("failed to get token for some unexpected reason", err);
                done = true;    
            }
        }
        try {
            // get results for current run
            var results = await rp(options);
            count++;
            var end = new Date();

            // prep the next cursor for next iteration
            if (results._links && results._links.next && results._links.next.href) {
                options.uri = results._links.next.href;
            } else {
                done = true;
                return range;
            }
            // print results
            let activities = results._embedded.activities;
            let stringResults = JSON.stringify(activities);
            let finalContent = ((count === 1) ? "[" : "") + stringResults.substring(1, stringResults.length - 1);
            finalContent += (done) ? ']' : ', ';
            console.log(finalContent);
        } catch (err) {
            // console.log('err', err);
            if (err.statusCode === 401 || err.statusCode === 403) {
                // token expired, let's reset it so a new one will be fetched at the beginning of the loop.
                token = null;
            } else {
                done = true;
                console.error("unexpected error. quitting loop", err);
            }
        }
    }
};

//***********************************//
//file access and status read/update //
//***********************************//
const initRequest = async () => {
    let status = { requested: [], finished: [] };
    let startDate = moment().tz('utc').startOf('minute').subtract(5, 'minutes').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z';
    let endDate = moment().tz('utc').startOf('minute').format('YYYY-MM-DDTHH:mm:ss.SSS') + 'Z';
    try {
        let savedStatus = await getStatus();
        if (savedStatus) {
            status = savedStatus;
            // if we already have finished results, set the interval from last finished to now.
            if (status.finished.length) {
                startDate = status.finished[status.finished.length - 1][1];
            }
            // if we already have a request in the queue then no need to repeat the interval, use its finished
            // time as the start of this interval
            if (status.requested.length) {
                startDate = status.requested[status.requested.length - 1][1];
            }
        }
    } catch (err) {
        console.error(err);
        // file doesn't exist yet, so do nothing. 
    }
    // add a request for the last 5 minutes or last finished to now.
    if (startDate != endDate) {
        await updateStatus(status, [startDate, endDate]);
    }
};
const updateStatus = async (status, request) => {
    if (request) {
        addRequest(status, request)
    }
    balanceStatus(status);
    await fsWrite(STATUS_FILE, JSON.stringify(status));
};
const addRequest = (status, request) => {
    // don't add a dup
    if (status.requested.filter(r =>  r[0] === request[0] && r[1] === request[1]).length === 0) {
        status.requested = status.requested.concat([request]);
    }
};
// Prune the finished list:
// if [n].end == [n+1].start => [n].end = [n+1].end, remove [n+1].
const balanceStatus = async (status) => {
    status.finished = status.finished.reduce((p,c) => {
        if (!p.length) {
            p.push(c);
        } else if (p[p.length-1][1] == c[0]) {
            p[p.length-1][1] = c[1]
        } else {
            p.push(c);
        }
        return p;
    }, []);
};
const getStatus = async () => {
    try {
        let status = await fsRead(STATUS_FILE);
        return JSON.parse(status);
    } catch (err) {
        console.error("failed to read file from cwd: ", process.cwd());
        return null;
    }
};

const fsWrite = (filename, content) => {
    return new Promise((resolve, reject) => {
        fs.writeFile(filename, content, (err) => {
            if (err) reject(err);
            else resolve(true);
        });
    });
};
const fsRead = (filename) => {
    return new Promise((resolve, reject) => {
        fs.p
        fs.readFile(filename, (err, content) => {
            if (err) reject(err);
            else resolve(content);
        });
    });
};

// main program
const program = async () => {
    await initRequest();
    let status = await getStatus();
    let finished = {};
    // iterate through every range in the requested node
    for (var i = 0; i < status.requested.length; i++) {
        let range = status.requested[i];
        let result = await getAllActivities(range);
        if (result) {
            // add this range to the finished list
            finished[range[0]+range[1]] = result;
        }

        // update anything that finished from requested to finished.
        let updatedStatus = status.requested.reduce((p,c) => {
            if (c[0]+c[1] in finished) {
                p.finished = p.finished.concat([c]);
            } else {
                p.requested = p.requested.concat([c]);
            }
            return p;
        }, {"requested": [], "finished": status.finished});
        updateStatus(updatedStatus);
    }
};

// run the program
program().catch(console.error);