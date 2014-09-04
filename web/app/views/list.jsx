/**
 * @jsx React.DOM
 */
var React = require('react');
var ReactCSSTransitionGroup = require('react/lib/ReactCSSTransitionGroup');

var fullReadingView = require('./fullReadingView.jsx');

var articleItem = React.createClass({

  setActive: function() {
    this.props.controller.setCurrent(this.props.article, function(){
      router.render();
    });
  },

  render: function() {
    var article = this.props.article,
        active = this.props.active;
    return (
      <li className={(this.props.className || '') + (active ? ' active' : '')} onClick={this.setActive}>
        {article.title}
      </li>
    )
  }
});

module.exports = React.createClass({

  render: function() {
    var activeArticle = this.props.controller.getCurrent();
    return (
      <div className="list-view">
        <ReactCSSTransitionGroup transitionName="list" component={React.DOM.ul} className="reading-list">
        {
          this.props.controller.getArticles().map(function(a, idx) {
            return (
              <articleItem article={a} active={a == activeArticle} key={a.id + a.last_action_timestamp} controller={this.props.controller}/>
            )
          }.bind(this))
        }
        </ReactCSSTransitionGroup>
        <fullReadingView
          controller={this.props.controller}
          readNow={false}
          article={activeArticle}
          canRead={this.props.controller.canRead}
          reading={true} />
      </div>
    );
  }
});
