var _ = require('underscore');

var config = _.extend(
                require("./config"),
                require("./app/sharedConfig")
            )

var express = require('express'),
    app = express(),
    port = config.app.port,
    Router = require('./lib/ServerRouter'),
    apiClient = require('./lib/server_api_client'),
    session = require('express-session'),
    cookieParser = require('cookie-parser'),
    request = require('request'),
    oauth = require('oauth'),
    twitterAPI = require('node-twitter-api');

// Allow directly requiring '.jsx' files.
require('node-jsx').install({extension: '.jsx'});

var routes = require('./app/routes')(apiClient, config.app.insecure),
    router = new Router(routes, apiClient);

app.use(cookieParser('hackweek'))

app.get('/dropbox_auth', function(req, res) {
    // rushing
    res.redirect('https://www.dropbox.com/1/oauth2/authorize?client_id=' + config.dropbox.client_id + '&response_type=code&redirect_uri=https://' + config.app.host + '/dropbox_auth_complete');
});

app.get('/dropbox_auth_complete', function(req, res) {
    var code = req.query.code;
    request.post(
        'https://api.dropbox.com/1/oauth2/token',
        { form: {
            code: code,
            grant_type: 'authorization_code',
            client_id: config.dropbox.client_id,
            client_secret: config.dropbox.client_secret,
            redirect_uri: 'https://' + config.app.host + '/dropbox_auth_complete'
        } },
        function (error, response, body) {
            if (!error && response.statusCode == 200) {
                var token = JSON.parse(body)['access_token'];
                request.post(
                    config.apiDomain + '/auth_with_dropbox',
                    {
                        form: {
                            token: token
                        }
                    }, function(error, response, body) {
                        var api_token = body;
                        res.cookie('token', api_token, { maxAge: 900000, httpOnly: false });
                        res.redirect('/');
                    });
            }
        }
    );
});

var twitter = new twitterAPI({
    consumerKey: config.twitter.consumerKey,
    consumerSecret: config.twitter.consumerSecret,
    callback: 'https://' + config.app.host + '/twitter_auth_complete'
});

// todo: use redis
var tokenStore = {}

app.get('/twitter_auth', function(req, res) {
    // if (!req.cookies.api_token) {
    //     return res.send({
    //         error: "unauthorized"
    //     });
    // }

    twitter.getRequestToken(function(error, requestToken, requestTokenSecret, results){
        if (error) {
            console.log("Error getting OAuth request token : " + JSON.stringify(error));
        } else {
            tokenStore[requestToken] = requestTokenSecret;
            return res.redirect("https://twitter.com/oauth/authenticate?oauth_token=" + requestToken)
        }
    });
});

app.get('/twitter_auth_complete', function(req, res) {
    var requestToken = req.query.oauth_token,
        requestTokenSecret = tokenStore[requestToken],
        oauth_verifier = req.query.oauth_verifier;
    if (!requestTokenSecret) {
        return res.send(500);
    }
    delete tokenStore[requestToken];

    twitter.getAccessToken(requestToken, requestTokenSecret, oauth_verifier, function(error, accessToken, accessTokenSecret, results) {
        if (error) {
            console.log(error);
        } else {
            console.log(accessToken, accessTokenSecret);
            request.post(
                config.apiDomain + '/source',
                {
                    form: {
                        'token_json': JSON.stringify([accessToken, accessTokenSecret]),
                        'source_type': 'twitter',
                        'token': req.cookies.token
                    }
                }, function(error, response, body) {
                    res.redirect('/');
                }
            );
        }
    });
});

app.post('/logout', function(req, res) {
    res.clearCookie('token');
    res.send({
        success: true
    });
});

app.use(express.static(__dirname + '/static'));

// Use the router as a middleware.
app.use(router.middleware);

var http = require('http'),
    fs = require('fs');
app.listen(port);
// http.createServer({
//     key: fs.readFileSync('keys/key.pem'),
//     cert: fs.readFileSync('keys/cert.pem')
// }, app).listen(port);

console.log('Running on port %s', port);
