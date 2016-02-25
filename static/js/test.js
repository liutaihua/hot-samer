/**
 * This file provided by Facebook is for non-commercial testing and evaluation
 * purposes only. Facebook reserves all rights not expressly granted.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * FACEBOOK BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

//function generate_photo_div(url) {
//    //sleep(5000) // for test loading bubble
//    $.ajaxSetup({async: false});
//    var main = "";
//    $.getJSON(url, function (data) {
//        $.each(data, function (key, val) {
//            main += '<a target="_blank" href="/samer/' + val['author_uid'] + '"><img class="lazy" data-original="' + val['photo'] + '" src="/static/image/ajax-loader.gif" weight=512 height=256 /></a>';
//        });
//    });
//    document.getElementById("container").innerHTML = main;
//    document.getElementById("loading-bubble").remove();
//}

var Comment = React.createClass({
  //rawMarkup: function() {
  //  var rawMarkup = marked(this.props.children.toString(), {sanitize: true});
  //  return { __html: rawMarkup };
  //},

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

var CommentForm = React.createClass({
  getInitialState: function() {
    return {author: '', text: ''};
  },
  handleAuthorChange: function(e) {
    this.setState({author: e.target.value});
  },
  handleTextChange: function(e) {
    this.setState({text: e.target.value});
  },
  handleSubmit: function(e) {
    e.preventDefault();
    var author = this.state.author.trim();
    var text = this.state.text.trim();
    if (!text || !author) {
      return;
    }
    this.props.onCommentSubmit({author: author, text: text});
    this.setState({author: '', text: ''});
  },
  render: function() {
    return (
      <form className="commentForm" onSubmit={this.handleSubmit}>
        <input
          type="text"
          placeholder="Your name"
          value={this.state.author}
          onChange={this.handleAuthorChange}
        />
        <input
          type="text"
          placeholder="Say something..."
          value={this.state.text}
          onChange={this.handleTextChange}
        />
        <input type="submit" value="Post" />
      </form>
    );
  }
});

ReactDOM.render(
  <CommentBox url="/hot-samer?offset=0&limit=500" pollInterval={10000} />,
  document.getElementById('container')
);

