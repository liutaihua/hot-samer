
var Comment = React.createClass({
  render: function() {
    return (
        <a target="_blank" href={'/samer/' + this.props.author_uid}>
            <img className="lazy" data-original={this.props.photo_url} src={this.props.photo_url} style={{weight:"512", height:"256"}} />
        </a>
    );
  }
});

var CommentBox = React.createClass({
  loadCommentsFromServer: function() {
    $.ajax({
      url: this.props.url,
      //dataType: 'json',
      type: 'GET',
      cache: false,
      success: function(data) {
        this.setState({data: JSON.parse(data)});
      }.bind(this),
      error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString());
      }.bind(this)
    });
  },
  getInitialState: function() {
    return {data: []};
  },
  componentDidMount: function() {
    this.loadCommentsFromServer();
    setInterval(this.loadCommentsFromServer, this.props.pollInterval);
  },
  render: function() {
    return (
      <div className="commentBox">
      <h4>使用React JS 作定时刷新页面</h4>
        <CommentList data={this.state.data} />
      </div>
    );
  }
});

var CommentList = React.createClass({
  render: function() {
    var commentNodes = this.props.data.map(function(comment) {
      return (
        <Comment author_uid={comment.author_uid} photo_url={comment.photo} key={comment.id}>
        </Comment>
      );
    });
    return (
      <div className="commentList">
        {commentNodes}
      </div>
    );
  }
});

ReactDOM.render(
  <CommentBox url="/hot-samer?offset=0&limit=50" pollInterval={10000} />,
  document.getElementById('container-react')
);

