/**
* Small wrapper around `superagent` module to make it easier to consume
* the API the same way on client & server.
*/
var superagent = require('superagent'),
    q = require('q'),
    config = require('./sharedConfig.json');

/**
* Proxy each method to `superagent`, formatting the URL.
*/
['get', 'post', 'put', 'path', 'del'].forEach(function(method) {
    module.exports[method] = function(req, path, query, callback) {
        console.log(path, query, callback);
        console.trace()
        var defer = q.defer();

        if (!callback && typeof(query) == "function") {
            callback = query;
            query = {};
        }

        var defer_callback = function(res) {
            callback && callback(res);
            defer.resolve(res);
        }
        if (window.initialData) {
            // callback(null, {body: null}); // first render
            // defer_callback(null, {body: null});
            defer_callback({body: window.initialData});
        } else {
            if (!query) {
                query = {}
            }
            query.token = req.session.token;
            if (method == 'get') {
                superagent[method](config.apiDomain + path).query(query).end(defer_callback);
            } else {
                superagent[method](config.apiDomain + path).type('form').send(query).end(defer_callback);
            }
        }
        return defer.promise;
    };
});
