/**
 * @jsx React.DOM
 */
var React = require('react');
var ReactCSSTransitionGroup = require('react/lib/ReactCSSTransitionGroup');

var fullReadingView = require('./fullReadingView.jsx');

module.exports = React.createClass({

  renderNomore: function() {
    return (
      <div className="article-card" key="nomore">
        <div className="article-card-message message-gray">
          No more article :(.{" "}
          <a href="/sources">Add some more sources</a>?
        </div>
      </div>
    );
  },

  renderArticle: function(article, type){
    if (!article) {
      return [];
    }
    if (!type) {
      type = "";
    }

    return (
      <div className={"article-card " + type} key={article.id}>
        <div className="card-content">
          <header className="card-title" dangerouslySetInnerHTML={{__html: article.title}} />
          { article.summary?
            <div className="summary" dangerouslySetInnerHTML={{__html: article.summary}} /> :
            <div className="empty-summary">No summary...</div>
          }
        </div>
        <div className="card-footer">
          <div className="footer-title">
            From:
          </div>
          {
            article.origins.map(function(o) {
              return (
                <div className="origin-panel">
                  <div className="image-holder">
                    <img src={o.image_url} />
                  </div>
                  <div className="origin-name">
                    { o.display_name }
                  </div>
                </div>
              )
            })
          }
        </div>
      </div>
    )
  },

  render: function() {
    var article = this.props.controller.getCurrent(),
        passed = this.props.controller.getLastPassed(),
        deferred = this.props.controller.getLastDeferred(),
        reading = this.props.controller.reading;
        can_read = this.props.controller.can_read;
    return (
      <fullReadingView
        className="stream-view"
        controller={this.props.controller}
        readNow={true}
        article={article}
        canRead={this.props.controller.canRead}
        reading={reading}>
        <ReactCSSTransitionGroup transitionName="stream" transitionLeave={false}>
          {this.renderArticle(passed, 'passed')}
          {article ? this.renderArticle(article, reading ? 'reading' : '') : this.renderNomore()}
          {this.renderArticle(deferred, 'deferred')}
        </ReactCSSTransitionGroup>
      </fullReadingView>
    );
  }
});
