/**
 * @jsx React.DOM
 */
var React = require('react');

module.exports = React.createClass({
  logout: function(e){
    e.preventDefault();
    e.stopPropagation();
    var router = this.props.router;
    router.sessionManager.logout(function(){
        router.refresh();
    });
  },

  renderLink: function(path, name) {
    return (
      <li className={path == this.props.router.getCurrentRoute() ? 'active' : null}>
        <a href={path}>{name}</a>
      </li>
    )
  },

  renderLoggedIn: function() {
    return (
      <div className="container">
        <div className="navbar-header">
          <button type="button" className="navbar-toggle" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
            <span className="sr-only">Toggle navigation</span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
            <span className="icon-bar"></span>
          </button>
          <span className="navbar-brand">Rdr</span>
        </div>

        <div className="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul className="nav navbar-nav">
            {this.renderLink('/', 'Stream')}
            {this.renderLink('/sources', 'Sources')}
            {this.renderLink('/list', 'List')}
          </ul>
          <ul className="nav navbar-nav navbar-right">
            <li>{this.props.session.user.name}</li>
            <li><a href='#' data-passthr={true} onClick={this.logout}>Logout</a></li>
          </ul>
        </div>
      </div>
    )
  },

  renderLoggedOut: function() {
    return (
      <div>Lol you out bro</div>
    )
  },

  render: function() {
    return (
        <nav className="navbar navbar-fixed-top navbar-default" role="navigation">
            { this.props.session ? this.renderLoggedIn() : this.renderLoggedOut() }
        </nav>
    );
  }
});
