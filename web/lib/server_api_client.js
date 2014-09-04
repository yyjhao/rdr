/**
* Small wrapper around `superagent` module to make it easier to consume
* the API the same way on client & server.
*/

var superagent = require('superagent'),
    q = require('q'),
    config = require('../app/sharedConfig.json');

var client = {};
/**
* Proxy each method to `superagent`, formatting the URL.
*/
['get', 'post', 'put', 'path', 'del'].forEach(function(method) {
    client[method] = function(req, path, query, callback) {
        if (!callback && typeof(query) == "function") {
            callback = query;
            query = {};
        }

        if (!query) {
            query = {}
        }

        query.token = req.cookies && req.cookies.token;
        var defer = q.defer();

        var defer_callback = function(res) {
            callback && callback(res);
            defer.resolve(res);
        }

        if (method == 'get') {
            superagent[method](config.apiDomain + path).query(query).end(defer_callback);
        } else {
            superagent[method](config.apiDomain + path).send(query).end(defer_callback);
        }
        return defer.promise;
    };
});

module.exports = client;
