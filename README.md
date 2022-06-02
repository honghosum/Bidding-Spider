# Scrapy

## 一、Scrapy 结构

### 1、组件结构及运作流程
![image](https://user-images.githubusercontent.com/42307155/171530076-bcbf753c-1f30-4be5-867b-41844b8db07d.png "组件结构")

#### (1).Spider
Spider由自己定义爬虫逻辑，主要是编写Request以及处理Response

#### (2).Scheduler
Scheduler调度器，用于处理Spider提交的Request队列（优先级、去重等），可自己定制

#### (3).Downloader
下载器接收Scheduler任务后，向互联网发送Request，下载网络资源，接收Response

#### (4).ItemPipeline
Spider在接收Response后进行处理，输出结果Item，由ItemPipeline进行最终处理及存储

#### (5).Middlewares
中间件主要分两个，一个是DownloaderMiddleware，一个是SpiderMiddleware<br>

可理解成Request与Response在整个Scrapy流程中的修改器

### 2、文件结构
![image](https://user-images.githubusercontent.com/42307155/171530696-a66349aa-e947-4973-9596-38c5426aa666.png "文件结构")

(1).文件夹Spiders中包含自己定义的各个Spider，运行的时候可根据Spider名选择用哪个<br>

(2).items.py 中定义了最终要输出的结果，相当于先给各个结果字段建个空列<br>

(3).middlewares.py 中定义DownloaderMiddleware以及SpiderMiddleware<br>

(4).pipelines.py 中定义结果流向、Item的处理方法、下载文件的处理方法等<br>

(5).settings.py 中定义组件的优先级、数据库、延时、User-Agent等参数

### 3、新建Scrapy项目

`> scrapy startproject Bidding`

## 二、spider.py

### 1、新建Spider

`> scrapy genspider bidding ggzy.gov.cn`

bidding为Spider名称，启动scrapy时需用到<br>

`> scrapy crawl bidding`

ggzy.gov.cn为该Spider爬取的网站域名

### 2、抛出Request

#### def start_requests(self):

Spider抛出的第一个Request，可由scrapy.FormRequest编辑提交内容<br>

`yield scrapy.FormRequest(url='', formdata='', meta={'', ''}, callback=self.parse)`

url为请求地址，该项目url = 'http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp'<br>

formdata为提交的表格内容，类型是字典<br>

meta为带入callback函数中的参数，类型是字典，即可在parse函数中使用该字典的变量<br>

callback为处理该request返回的response的函数，即经过Downloader返回response到Spider中进行进一步处理

### 3、解析Response

#### def parse(self):

该函数用于处理返回的response，也可再次抛出request<br>

可设置多个parse函数，通过调整yield request中的callback参数来选择由哪一个parse函数处理response<br>

该项目中，共有4个parse函数:

##### I.parse

该函数用于翻页、切换搜索关键词以及进入下一层页面解析

##### II.parse_pro_id

因为工程建设文档与政府采购文档差异较大，所以要分两类进入再下一层页面解析

##### III.parse_purchase_content

政府采购文档的解析函数

##### IV.parse_bidding_content

工程建设文档的解析函数

### 4、抛出Item

先引用item的定义文件：<br>

`from Bidding import items`

在解析函数中创建item：<br>

`item = items.BiddingItem()`

在解析函数中设置item参数：<br>

`item['pro_id'] = pro_id`

抛出item到ItemPipelines中：<br>

`yield item`

## 三、items.py

创建Item类并定义各字段

    Class BiddingItem(scrapy.Item):
        pro_id = scarpy.Field()
        ......

## 四、middlewares.py

### 1、class BiddingSpiderMiddleware:

### 2、class BiddingDownloaderMiddleware:

## 五、pipelines.py

### 1、定义数据库：

    import pymongo
    from Bidding import settings
    
    class BiddingPipeline:
    
        client = pymongo.MongoClient(host=settings.MONGODB_HOST, port=settings.MONGODB_PORT)
        db = client[settings.MONGODB_DBNAME]
        self.sheet = db[settings.MONGODB_SHEETNAME]

### 2、处理Item：

在函数process_item中定义spider抛出item的处理方法<br>

该项目在此处进行去重

### 3、处理下载文件：

    from scrapy.pipelines.files import FilesPipeline
    
    class FileDownloadPipeline(FilesPipeline):

        def get_media_requests(self, item, info):
            urls = ItemAdapter(item).get(self.files_urls_field, [])
            names = ItemAdapter(item).get(self.files_names_field, [])
            for i in range(0, len(urls)):
                return [Request(url=urls[i], meta={'name': names[i]})]

        def file_path(self, request, response=None, info=None, *, item=None):
            return '%s' % request.meta['name']

## 六、settings.py
