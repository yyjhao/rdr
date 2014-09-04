/**
 * @jsx React.DOM
 */
var React = require('react');

var sourceList = require('./sourceList.jsx'),
    articleStreamView = require('./articleStreamView.jsx');

module.exports = React.createClass({
  renderApp: function() {
    return (
      <div>
        <articleStreamView controller={this.props.controller} />
      </div>

    )
  },

  renderLogin: function() {
    return (
      <div className="container">
        <a href="/dropbox_auth" data-passthru={true}>
            Login with Dropbox
        </a>
      </div>
    )
  },

  render: function() {
    return this.props.session ? this.renderApp() : this.renderLogin();
  }
});
