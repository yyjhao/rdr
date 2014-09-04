/**
 * @jsx React.DOM
 */
var React = require('react');

module.exports = React.createClass({

  renderList: function() {
    return (
      <ul className="source-list">
        { this.props.controller.getSources().map(function(s, idx) {
          return (
            <li className={s.type} key={s.type + '-' + s.id}>
              {s.name}
            </li>
          )
        }) }
      </ul>
    );
  },

  renderEmpty: function() {
    return (
      <div className="empty">
        No source yet...
      </div>
    );
  },

  render: function() {
    return (
      <section className="container">
        <header>
          Your sources
        </header>
        <div>
          Add more..
        </div>
        <button type="button" className="btn btn-primary btn-sm" onClick={this.addSourceGen('twitter')} key={'twitter'}>Twitter</button>
        <button type="button" className="btn btn-primary btn-sm" onClick={this.addSourceGen('rss')} key={'rss'}>rss</button>
        <button type="button" className="btn btn-primary btn-sm" onClick={this.addSourceGen('opml')} key={'opml'}>Import opml from your dropbox</button>
        {
          this.props.controller.getSources() ? this.renderList() : this.renderEmpty()
        }
      </section>
    );
  },

  addSourceGen: function(type) {
    return function() {
      this.props.controller.add(type);
    }.bind(this);
  } 
});
