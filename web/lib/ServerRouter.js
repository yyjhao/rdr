var Router = require('../app/router'),
    React = require('react'),
    DirectorRouter = require('director').http.Router,
    ejs = require("ejs"),
    fs = require("fs"),
    apiClient = require('./server_api_client');

var layoutTemplate = fs.readFileSync(__dirname + '/../app/views/layout.ejs', 'ascii');

module.exports = ServerRouter;

function ResHandler(context, router){
    this.context = context;
    this.router = router;
}

ResHandler.prototype = {
    err: function(err) {
        this.router.handleErr(err);
    },

    redirect: function(location){
        this.context.res.redirect(location);
    },

    render: function(viewPath, data, controller_str) {
        var res = this.context.res;

        apiClient.get({}, '/auth?token=' + this.context.req.cookies.token, function(apires) {
            var session = null;
            if (!apires.error &&
                !apires.body.error) {
                session = {
                    token: this.context.req.cookies.token,
                    user: apires.body.user
                }
            }
            var controller;
            if (controller_str) {
                var Controller = require("../app/controllers/" + controller_str);
                controller = new Controller(apiClient, data);
            }
            var reactRoot = React.renderComponentToString(this.router.renderView(viewPath, controller, session));
            var html = ejs.render(layoutTemplate, {
                initialData: data,
                session: session,
                reactRoot: reactRoot
            });
            res.send(html);
        }.bind(this))
    },

    ensureHTTPS: function(){
        if(this.context.req.header('x-forwarded-proto') !== "https"){
            this.context.res.redirect("https://" + this.context.req.headers.host + this.context.req.path);
            return false;
        } else {
            return true;
        }
    }
};

function ServerRouter(routes, apiClient) {
    Router.call(this, routes, apiClient, DirectorRouter, '../app/views', function(handler) {
        return {
            get: this.getRouteHandler(handler)
        };
    }.bind(this));

    // Express middleware.
    this.middleware = function(req, res, next) {
        // Attach `this.next` to route handler, for better handling of errors.
        this.directorRouter.attach(function() {
            this.next = next;
        });

        this.directorRouter.dispatch(req, res, function (err) {
            if (err) {
                next(err);
            }
        });
    }.bind(this);
}

ServerRouter.prototype = Object.create(Router.prototype);

ServerRouter.prototype.getReq = function(context) {
    return context.req;
};

ServerRouter.prototype.getRes = function(context) {
    return new ResHandler(context, this);
};
