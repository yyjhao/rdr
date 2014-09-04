// TODO: refactor

function ArticleList(apiClient, data) {
    this.dataStore = data.articles;
    this.apiClient = apiClient;
    this.active = this.dataStore[0];
    this.active_idx = 0;
    this.canRead = true;
}

ArticleList.prototype.getArticles = function() {
    return this.dataStore;
}

ArticleList.prototype.getCurrent = function() {
    return this.active;
};

ArticleList.prototype.setCurrent = function(val, callback) {
    this.active_idx = this.dataStore.indexOf(val);
    this.active = val;

    this.apiClient.get(router.getReq(), '/iframe_ok', {
        url: this.getCurrent().url
    }, function(res) {
        this.canRead = res.body.iframe_ok;
        callback && callback();
    }.bind(this));
}

ArticleList.prototype._next = function(callback) {
    if (this.active_idx + 1 >= this.dataStore.length) {
        if (this.active_idx > 0) this.active_idx--;
    } else {
        this.active_idx++;
    }
    this.active = this.dataStore[this.active_idx];
    this.load(callback);
}

ArticleList.prototype.performActionOnCurrent = function(action, callback) {
    if (this.worker) return;
    this.reading = false;
    this.worker = this.apiClient.post(router.getReq(), '/article', {
        article_id: this.getCurrent().id,
        action: action
    });
    this.worker.done(function() {
        this.worker = null;
        this._next(callback);
    }.bind(this));
}

ArticleList.prototype.like = function(callback) {
    this.performActionOnCurrent('like', callback);
};

ArticleList.prototype.dislike = function (callback) {
    this.performActionOnCurrent('like', callback);
};

ArticleList.prototype.load = function(callback) {
    if (!this.loader) {
        this.loader = this.apiClient.get(router.getReq(), '/article', { article_type: 'defer' });
        this.loader.done(function(res) {
            this.dataStore.length = 0;
            [].push.apply(this.dataStore, res.body.articles);
            this.setCurrent(this.dataStore.filter(function(a) {
                return a.id == this.active.id;
            }.bind(this))[0]);
            this.loader = null;
            callback && callback();
        }.bind(this));
    }
};

ArticleList.prototype.updateData = function(newData) {
    this.dataStore = newData;
    this.setCurrent(this.dataStore.filter(function(a) {
        return a.id == this.active.id;
    }.bind(this))[0]);
}

ArticleList.prototype.pass = function(callback) {
    this.performActionOnCurrent('pass', callback);
};

ArticleList.prototype.defer = function(callback) {
    this.performActionOnCurrent('defer', callback);
};

ArticleList.prototype.getLastPassed = function() {
    return this._lastPassed;
};

ArticleList.prototype.getLastDeferred = function() {
    return this._lastDeferred;
};

module.exports = ArticleList;
