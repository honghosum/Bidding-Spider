# Scrapy

## Scrapy 结构

### 一、组件结构及运作流程
![image](https://user-images.githubusercontent.com/42307155/171530076-bcbf753c-1f30-4be5-867b-41844b8db07d.png "组件结构")
#### I.Spider
Spider由自己定义爬虫逻辑，主要是编写Request以及处理Response。
#### II.Scheduler
Scheduler调度器，用于处理Spider提交的Request队列（优先级、去重等），可自己定制。
#### III.Downloader
下载器接收Scheduler任务后，向互联网发送Request，下载网络资源，接收Response。
#### IV.ItemPipeline
Spider在接收Response后进行处理，输出结果Item，由ItemPipeline进行最终处理及存储。
#### V.Middlewares
中间件主要分两个，一个是DownloaderMiddleware，一个是SpiderMiddleware。  
可理解成Request与Response在整个Scrapy流程中的修改器。

### 二、文件结构
