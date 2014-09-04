/**
 * @jsx React.DOM
 */
var React = require('react');

var navHeader = require("./navHeader.jsx");

module.exports = React.createClass({
  render: function() {
    return (
    <div>
        <navHeader session={this.props.session} router={this.props.router} />
        <div>
          {this.props.children}
        </div>
    </div>
    );
  }
});

