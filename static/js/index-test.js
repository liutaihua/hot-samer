//var React = require('react');
//var Loading = require('react-loading');
//require(['static/js/react-loading']);

var LoadingComponent = React.createClass({
  render: function() {
    return (
        <Loading type='bubbles' color='#030102'>
        </Loading>
    );
  }
});

var Pic = React.createClass({
    onPraiseHeartClick: function(photoId) {
        $.ajax({
            url: '/photo/'+photoId+'/likes',
            dataType: 'json',
            type: 'POST',
            data: {"photo_id": photoId},
            success: function(data) {
                console.log("put likes count success")
            }.bind(this),
            error: function (xhr, status, err) {
                console.error(photoId, status, err.toString());
            }.bind(this)
        });
    },
    render: function () {
        var clickHandler = this.onPraiseHeartClick.bind(this, this.props.photo_id);
        return (
            <li className="li-photo box">
                 <span className="praise-heart">
                     <a href="#" onClick={clickHandler}>
                         <img style={{weight:"16", height:"16"}} src="/static/image/heart-icon.png" />
                     </a>
                 </span>
                <div>
                    <a target="_blank" href={'/samer/' + this.props.author_uid}>
                    <img className="lazy" data-original={this.props.photo_url} src={this.props.photo_url}
                         style={{weight:"512", height:"256"}}/>
                    </a>
                 </div>
            </li>
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
            <PicList data={this.state.data}/>
        );
    }
});

var PicList = React.createClass({
    render: function () {
        var PicNode = this.props.data.map(function (picData) {
            if (picData.author_uid == "show-loading-prompt") {
                return (
                    <LoadingComponent key={picData.id}></LoadingComponent>
                );
            } else {
                return (
                    <Pic author_uid={picData.author_uid} photo_url={picData.photo} photo_id={picData.id} key={picData.id}>
                    </Pic>
                );
            }
        });
        return (
            <div className="PicList wrap">
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

var PicNav = React.createClass({
    render: function () {
        return (
            <a className="pic-nav-name" onClick={this.props.onClick} href={this.props.href_uri}>{this.props.PicNavName}</a>
        );
    }
});

var NavBox = React.createClass({
    handleClick: function(restApi){
        var picBox = this.refs.PicBox;
        console.log('get from restful: '+restApi);
        picBox.setState({data: [{author_uid: "show-loading-prompt", id: 999}]}); // load前给假数据, 用于显示Loading提示
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
            var exclude_ajax = ["/", "/lab", "/search", "/music", "/hottest-rank"];
            if (exclude_ajax.indexOf(m.href) > -1) {
                return (
                    <Nav href_uri={m.href} nav_name={m.nav_name} key={m.id}>
                    </Nav>
                );
            }
        });

        var PicNavNode = this.props.items.map(function (m) {
            var boundClick = thisSelf.handleClick.bind(this, m.href);
            var pic_nav_names = ["最新", "最热", "自画", "摄影", "其他", "未成年(慎入)"];
            if (pic_nav_names.indexOf(m.nav_name) > -1) {
                return (<PicNav href_uri="#"  PicNavName={m.nav_name} key={m.id} onClick={boundClick}>
                </PicNav>);
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
            <div className="PicBox">
                <div className="title"><h1>hot-samer</h1></div>
                <div>
                    {PicNavNode}
                </div>
                <div id="loading-div"></div>
                <PicBox url="/hot-samer?offset=0&limit=200" pollInterval={20000} ref="PicBox"> </PicBox>
            </div>
            </div>
        );
    }
});

var data = [
    {href: "/", nav_name: "热图", id: 0},
    {href: "/hot-samer?offset=0&limit=500", nav_name: "最新", id: 1},
    {href: "/hot-samer?by_likes=1&offset=0&limit=500", nav_name: "最热", id: 2},
    {href: "/hot-samer?offset=0&limit=500&hot_level=1", nav_name: "自画", id: 3},
    {href: "/hot-samer?offset=0&limit=500&hot_level=2", nav_name: "摄影", id: 4},
    {href: "/hot-samer?offset=0&limit=500&hot_level=3", nav_name: "其他", id: 5},
    {href: "/hottest-rank", nav_name: "红人", id: 6},
    {href: "/music", nav_name: "在听", id: 7},
    {href: "/search", nav_name: "寻人", id: 8},
    {href: "/lab", nav_name: "实验室", id: 9},
    {href: "/tumblr", nav_name: "未成年(慎入)", id: 10},
];
ReactDOM.render(< NavBox items={ data }
    />,
    document.getElementById('body')
);

//ReactDOM.render(
//    <PicBox url="/hot-samer?offset=0&limit=200" pollInterval={20000}/>,
//    document.getElementById('container-react')
//);
