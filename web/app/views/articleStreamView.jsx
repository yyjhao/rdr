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
      <header>
        <a href={article.url} target="_blank">{article.url}</a>
      </header>
        {
          article.articles.map(function(a) {
            return (<div className="article-single">
              <div className="origin-panel">
                  <div className="image-holder">
                    <img src={a.origin_img} />
                  </div>
                  <div className="origin-name">
                    { a.origin_display_name }
                  </div>
                </div>
              <div className="article-content">
                <div className="article-title" dangerouslySetInnerHTML={{__html: a.title}} />
                <div className="article-summary" dangerouslySetInnerHTML={{__html: a.summary}} />
              </div>
            </div>)
          })
        }
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
