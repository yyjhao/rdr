/**
 * @jsx React.DOM
 */
var React = require('react');
var ReactCSSTransitionGroup = require('react/lib/ReactCSSTransitionGroup');

module.exports = React.createClass({
  pass: function() {
    this.props.controller.pass(function(){
      router.render()
    });
  },

  defer: function() {
    this.props.controller.defer(function(){
      router.render()
    });
  },

  like: function() {
    this.props.controller.like(function(){
      router.render()
    });
  },

  dislike: function() {
    this.props.controller.dislike(function(){
      router.render()
    });
  },

  read: function() {
    this.props.controller.read(function() {
      router.render();
    });
  },

  renderReading: function(article) {
    if (!article) {
      return [];
    }
    if (this.props.canRead) {
      return (
        <div className="reading-view">
          <div className="reader">
            <div><a href={article.url}>{article.url}</a></div>
            <iframe src={article.url} sandbox="allow-forms allow-scripts" />
          </div>
          <div className="split-row">
            <div className="like-button col-md-6" onClick={this.like} key="like-button">
              <span>Good!</span>
            </div>
            <div className="dislike-button col-md-6" onClick={this.dislike} key="dislike-button">
              <span>Nah..</span>
            </div>
          </div>
        </div>
      )
    } else {
      return (
        <div className="reading-view">
          <div className="article-card" key="nomore">
            <div className="article-card-message message-gray">
              Unfortunately the publisher does not allow viewing of this page in rdr website.
              <br />
              You can <a href={article.url} data-passthru={true} target="_blank">view the website directly</a>.<br />
              Just let us know if it{"'"}s good after that!
            </div>
          </div>
          <div className="split-row">
            <div className="like-button col-md-6" onClick={this.like} key="like-button">
              <span>Good!</span>
            </div>
            <div className="dislike-button col-md-6" onClick={this.dislike} key="dislike-button">
              <span>Nah..</span>
            </div>
          </div>
        </div>
      )
    }
  },

  render: function() {
    return (
      <div className={"articles-view" + (this.props.reading ? " reading" : "") + " " + (this.props.className || "")}>
        { this.props.reading ? this.renderReading(this.props.article) : [] }
        {
          this.props.readNow ? (
            <div className="read-button" onClick={this.read} key="read-button">
              <span>Read now</span>
            </div>
          ) : []
        }
        <div className="pass-button" onClick={this.pass} key="pass-button">
          <span>Pass</span>
        </div>
        <div className="defer-button" onClick={this.defer} key="defer-button">
          <span>Later</span>
        </div>
        {
          this.props.children
        }
      </div>
    );
  }
});
