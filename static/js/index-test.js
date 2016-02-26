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
    loadPicturesFromServer: function (url) {
        $.ajax({
            url: url,
            //dataType: 'json',
            type: 'GET',
            cache: false,
            success: function (data) {
                console.log("get data success pre setState");
                this.setState({data: JSON.parse(data)});
                console.log("get data success has setState");
            }.bind(this),
            error: function (xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    componentWillUpdate: function(nextProps, nextState) {
        console.log("PicBox state will change,"+nextProps+nextState);
    },
    componentDidUpdate: function(prevProps, prevState) {
        console.log("PicBox state has change,"+prevProps+prevState);
    },
    getInitialState: function () {
        return {data: []};
    },
    intervalTask: null,
    setIntervalTask: function (uri) {
        console.log('set intervalTask uri: ' + uri);
        var loadInterval = this.loadPicturesFromServer.bind(this, uri);
        this.intervalTask = setInterval(loadInterval, this.props.pollInterval);
    },
    cancelIntervalTask: function () {
        console.log('cancel intervalTask: ' + this.intervalTask);
        if (this.intervalTask) {
            clearInterval(this.intervalTask)
        }
    },
    componentDidMount: function () {
        this.loadPicturesFromServer(this.props.url);
        this.setIntervalTask(this.props.url);
        //document.getElementById("loading-bubble").remove();  // 清除loading提示
    },
    render: function () {
        return (
            <div className="PicBox">
                <div className="title"><h1>hot-samer</h1></div>
                <h5>本页面使用React JS 局部div刷新, 定时ajax刷新div</h5>
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


var Nav = React.createClass({
    render: function () {
        return (
                <a onClick={this.props.onClick}
                    href={this.props.href_uri}
                   data-moreurl-dict="{&quot;from&quot;:&quot;top-nav-click-main&quot;,&quot;uid&quot;:&quot;45674332&quot;}">{this.props.nav_name}
                </a>
        );
    }
});

var NavBox = React.createClass({
    handleClick: function(restApi){
        var picBox = this.refs.PicBox;
        console.log('get from restful: '+restApi);
        picBox.setState({data: []}); // 清下之后再load
        picBox.cancelIntervalTask();
        picBox.loadPicturesFromServer(restApi);
        //document.getElementById("loading-div").remove();
        // set intervalTask again
        picBox.setIntervalTask(restApi);
    },


    render: function () {
        const thisSelf = this;  //
        var NavNode = this.props.items.map(function (m) {
            var boundClick = thisSelf.handleClick.bind(this, m.href);
            var exclude_ajax = ["/lab", "/search", "/music", "/hottest-rank"];
            if (exclude_ajax.indexOf(m.href) > -1) {
                return (
                    <Nav href_uri={m.href} nav_name={m.nav_name} key={m.id}>
                    </Nav>
                );
            } else {
                return (
                    <Nav href_uri={"#"} nav_name={m.nav_name} key={m.id} onClick={boundClick}>
                    </Nav>
                );
            }
        });

        return (
            <div>
            <div id="hs-global-nav" className="global-nav">
                <div className="global-nav-items">
                    <ul style={{position: "fixed"}} id="container-nav">
                        <li className="on">
                            {NavNode}
                        </li>
                    </ul>
                </div>
            </div>
            <PicBox url="/hot-samer?offset=0&limit=200" pollInterval={20000} ref="PicBox">
            </PicBox>
            </div>
        );
    }
});

var data = [
    {href: "/hot-samer?offset=0&limit=500", nav_name: "最新", id: 1},
    {href: "/hot-samer?by_likes=1&offset=0&limit=500", nav_name: "最热", id: 2},
    {href: "/hot-samer?offset=0&limit=500&hot_level=1", nav_name: "自画", id: 3},
    {href: "/hot-samer?offset=0&limit=500&hot_level=2", nav_name: "摄影", id: 4},
    {href: "/hot-samer?offset=0&limit=500&hot_level=3", nav_name: "其他", id: 5},
    {href: "/hottest-rank", nav_name: "红人", id: 6},
    {href: "/music", nav_name: "在听", id: 7},
    {href: "/search", nav_name: "寻人", id: 8},
    {href: "/lab", nav_name: "实验室", id: 9},

];
ReactDOM.render(< NavBox items={ data }
    />,
    document.getElementById('body')
);

//ReactDOM.render(
//    <PicBox url="/hot-samer?offset=0&limit=200" pollInterval={20000}/>,
//    document.getElementById('container-react')
//);
