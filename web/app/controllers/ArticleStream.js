function ArticleStream(apiClient, data) {
    if (!data) {
        this.dataStore = [];
    } else {
        this.dataStore = data.articles;
    }
    this.apiClient = apiClient;
    this.bindEvents();
}

ArticleStream.prototype.bindEvents = function() {
    try {
        $(window).on('keyup', function(e) {
            if (!this.reading) {
                if (e.which == 37) {
                    this.pass(function() {
                        router.render();
                    });
                } else if (e.which == 39) {
                    this.defer(function() {
                        router.render()
                    });
                } else if (e.which == 40) {
                    this.read(function() {
                        router.render();
                        $('.reading-view iframe').focus();
                    });
                }
            } else if (e.which == 27) {
                this.stopReading(function() {
                    router.render();
                });
            }
        }.bind(this))
    } catch(err) {
        console.log(err);
        //lol
    }
};

ArticleStream.prototype.getCurrent = function() {
    return this.dataStore[0];
};

ArticleStream.prototype.stopReading = function(callback) {
    this.reading = false;
    callback && callback();
}

ArticleStream.prototype.read = function(callback) {
    if (!this.getCurrent()) {
        return;
    }
    this.reading = true;
    this.worker = null;
    this.loader = this.apiClient.get(router.getReq(), '/iframe_ok', {
        url: this.getCurrent().url
    }, function(res) {
        this.loader = null;
        this.canRead = res.body.iframe_ok;
        callback && callback();
    }.bind(this));
};

ArticleStream.prototype._next = function(callback) {
    console.log("_next", this.dataStore.length);
    if (this.dataStore.length) {
        callback();
    } else {
        this.load(callback);
    }
}

ArticleStream.prototype.performActionOnCurrent = function(action, callback) {
    if (this.worker || this.loader) return;
    if (!this.getCurrent()) {
        return;
    }
    this.reading = false;
    this.worker = this.apiClient.post(router.getReq(), '/article', {
        article_id: this.getCurrent().id,
        action: action
    });
    var removed = this.getCurrent();
    if (this.dataStore.length) {
        this.dataStore.shift();
    }
    console.log(action, 'requesting');
    this.worker.then(function() {
        console.log(action, this.dataStore);
        this.worker = null;
        this._next(callback);
    }.bind(this), function() {
        console.log(action, 'fail');
        this.worker = null;
    }.bind(this));
    return removed;
};

ArticleStream.prototype.like = function(callback) {
    console.assert(this.reading);
    this.performActionOnCurrent('like', callback);
};

ArticleStream.prototype.dislike = function (callback) {
    console.assert(this.reading);
    this.performActionOnCurrent('dislike', callback);
};

ArticleStream.prototype.load = function(callback) {
    if (!this.loader) {
        this.loader = this.apiClient.get(router.getReq(), '/article');
        this.loader.then(function(res) {
            [].push.apply(this.dataStore, res.body.articles);
            console.log(res.body.articles)
            this.loader = null;
            callback && callback();
        }.bind(this), function() {
            this.loader = null;
        }.bind(this));
    }
};

ArticleStream.prototype.pass = function(callback) {
    this._lastPassed = this.performActionOnCurrent('pass', callback) || this._lastPassed;
    console.log("last passed", this._lastPassed);
};

ArticleStream.prototype.defer = function(callback) {
    this._lastDeferred = this.performActionOnCurrent('defer', callback) || this._lastDeferred;
};

ArticleStream.prototype.getLastPassed = function() {
    return this._lastPassed;
};

ArticleStream.prototype.getLastDeferred = function() {
    return this._lastDeferred;
};

module.exports = ArticleStream;
