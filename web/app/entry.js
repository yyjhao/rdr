/**
 * Entry point for client-side.
 */

var ClientRouter = require('./ClientRouter'),
    apiClient = require("./api_client"),
    routes = require('./routes')(apiClient, location.hostname === "localhost"),
    sessionManager = require('./sessionManager')(apiClient, window.initialSession),
    SourceManager = require('./controllers/sourceManager'),
    router = new ClientRouter(routes, apiClient, sessionManager);

window.router = router;
router.start();
