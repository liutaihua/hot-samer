# hot-samer
hot-samer

一个色色的页面 其实不是我色色的， 图都是应用 Same 的

由于same公司没有对图片做反垃圾和反黄， 存在个别黄图。 不过大多数都是samer的自拍，虽然尺度略大。

简单的通过 restful接口获取到帖子的数据， 然后存在elasticSearch里。

有这些数据， 可以做很多帖子排名啊，用户查看啊， 红人列表啊什么的有意思的事情

需要自己部署玩的话: requirements 文件是我的pip freeze， 比较懒就没有仔细过滤了 使用 pip install -r requirements 自动安装就可以了

爬虫脚本是 same_spider/collect_data_into_es.py  

执行 python collect_data_into_es.py get_x 会把几个比较热门的频道内帖子信息爬下来  

前提是需要本地启动 elasticSearch, elasticSearch启动十分简单， 下载之后有jdk环境直接启动就行了.  

另外elasticSearch需要安装一个 [plugin ](https://github.com/NLPchina/elasticsearch-sql)已支持sql语法搜索es
