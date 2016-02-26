var Pic = React.createClass({
    render: function () {
        return (
            <a target="_blank" href={'/samer/' + this.props.author_uid}>
                <img className="lazy" data-original={this.props.photo_url} src={this.props.photo_url}
                     style={{weight:"512", height:"256"}}/>
            </a>
        );
    }
});

var PicBox = React.createClass({
    loadPicturesFromServer: function () {
        $.ajax({
            url: this.props.url,
            //dataType: 'json',
            type: 'GET',
            cache: false,
            success: function (data) {
                this.setState({data: JSON.parse(data)});
            }.bind(this),
            error: function (xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    getInitialState: function () {
        return {data: []};
    },
    componentDidMount: function () {
        this.loadPicturesFromServer();
        setInterval(this.loadPicturesFromServer, this.props.pollInterval);
        document.getElementById("loading-bubble").remove();  // 清除loading提示
    },
    render: function () {
        return (
            <div className="PicBox">
                <h4>使用React JS 作定时刷新页面</h4>
                <PicList data={this.state.data}/>
            </div>
        );
    }
});

var PicList = React.createClass({
    render: function () {
        var PicNode = this.props.data.map(function (picData) {
            return (
                <Pic author_uid={picData.author_uid} photo_url={picData.photo} key={picData.id}>
                </Pic>
            );
        });
        return (
            <div className="PicList">
                {PicNode}
            </div>
        );
    }
});

ReactDOM.render(
    <PicBox url="/hot-samer?offset=0&limit=200" pollInterval={20000}/>,
    document.getElementById('container-react')
);

