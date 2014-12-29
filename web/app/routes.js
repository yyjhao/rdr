var _ = require("underscore"),
    q = require("q");

module.exports = function(apiClient, insecure) {
    return {
        '/': function(req, res) {
            if (req.session || (req.cookies && req.cookies.token)) {
                apiClient.get(req, '/article', function(articles_res) {
                    res.render('index', {
                        articles: articles_res.body.items || []
                    }, 'ArticleStream');
                });
            } else {
                res.render('index', {});
            }
        },
        '/sources': function(req, res) {
            if (req.session || (req.cookies && req.cookies.token)) {
                apiClient.get(req, '/source', function(sources_res) {
                    res.render('sourceManagerView', {
                        sources: sources_res.body.sources,
                    }, 'sourceManager');
                });
            } else {
                res.redirect('/');
            }
        },
        '/list': function(req, res) {
            if (req.session || (req.cookies && req.cookies.token)) {
                apiClient.get(req, '/article', { 'article_type': 'defer' }, function(articles_res) {
                    res.render('list', {
                        articles: articles_res.body.articles || []
                    }, 'ArticleList');
                });
            } else {
                res.redirect('/');
            }
        }
    };
};
