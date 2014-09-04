/**
 * @jsx React.DOM
 */
var React = require('react');

var pageBody = require("./pageBody.jsx");

module.exports = React.createClass({
  render: function() {
    return (
    <html lang="en">
        <head>
            <meta charset="utf-8" />
            <title>Rdr</title>
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <meta name="description" content="" />
            <meta name="author" content="" />
            <link rel="stylesheet" href="/css/vex.css" />
            <link rel="stylesheet" href="/css/vex-theme-os.css" />
            <link href="/css/bootstrap.min.css" rel="stylesheet" />
            <link href="/css/style.css" rel="stylesheet" />
            
        </head>
        <body>
            <div id="body-container">
                {this.props.children}
            </div>
            <div id="loading-screen">
                <img className="loading-gear" src="/img/loading.png" />
                <div className="loading-status"></div>
            </div>
            <script dangerouslySetInnerHTML={{__html: "window.initialData=" + JSON.stringify(this.props.initialData) + "; window.initialSession=" + JSON.stringify(this.props.session)}} />
            <script src="/js/jquery-1.10.2.min.js"></script>
            <script src="/js/vex.combined.min.js"></script>
            <script dangerouslySetInnerHTML={{__html: "vex.defaultOptions.className = 'vex-theme-os';"}} />
            <script src="/js/bootstrap.min.js"></script>
            <script src="/scripts.js"></script>
        </body>
    </html>
    );
  }
});

