function SourceManager(apiClient, data) {
    this.dataStore = data.sources;
    this.add_handler = {
        'twitter': function() {
            window.location = '/twitter_auth';
        }.bind(this),

        'rss': function() {
            vex.dialog.open({
                message: 'Type in the rss url below',
                input: "<input name=\"url\" type=\"text\" placeholder=\"url\" required />\n",
                callback: function(data) {
                    if (data) {
                        apiClient.post(router.getReq(), '/source', {
                            source_type: 'rss',
                            url: data.url
                        }, function(res) {
                            if (res.body.error) {
                                router.render();
                                vex.dialog.alert('Bad url.');
                            } else {
                                this.dataStore.length = 0;
                                [].push.apply(this.dataStore, res.body.sources);
                                router.render();
                            }
                        }.bind(this));
                    }
                }
            });
        }.bind(this),

        'opml': function() {
            Dropbox.choose(options = {
                success: function(files) {
                    apiClient.post(router.getReq(), '/import_opml', {
                        url: files[0].link
                    }, function(res) {
                        this.dataStore.length = 0;
                        [].push.apply(this.dataStore, res.body.sources);
                        router.render();
                    }.bind(this))
                }.bind(this),
                linkType: "direct",
                multiselect: false,
                extensions: ['opml'],
            });
        }.bind(this)
    };
}

SourceManager.prototype.add = function(type) {
    this.add_handler[type]();
};

SourceManager.prototype.remove = function(source) {
    // TODO
};

SourceManager.prototype.getSources = function() {
    return this.dataStore;
};

module.exports = SourceManager;
