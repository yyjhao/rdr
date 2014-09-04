/**
 * @jsx React.DOM
 */
var React = require('react');

var sourceList = require('./sourceList.jsx');

module.exports = React.createClass({
  render: function() {
    return (
      <div>
        <sourceList
          controller={this.props.controller}
        />
      </div>

    )
  }
});
