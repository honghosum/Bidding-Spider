# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BiddingItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    content = scrapy.Field()  # 文本
    date = scrapy.Field()  # 发布日期
    province = scrapy.Field()  # 省份
    platform = scrapy.Field()  # 平台
    classify = scrapy.Field()  # 招标类型
    stage = scrapy.Field()  # 项目阶段
    keyword = scrapy.Field()  # 关键词
    content_url = scrapy.Field()  # 网址
    origin_url = scrapy.Field()  # 原始地址
    pro_name = scrapy.Field()  # 项目名称
    pro_id = scrapy.Field()  # 项目编号
    period = scrapy.Field()  # 工期

    pur_name = scrapy.Field()  # 招标方名称
    pur_add = scrapy.Field()  # 招标方地址
    pur_tel = scrapy.Field()  # 招标方电话

    sup_name = scrapy.Field()  # 供应商名称
    sup_add = scrapy.Field()  # 供应商地址

    attn_name = scrapy.Field()  # 项目联系人名称
    attn_tel = scrapy.Field()  # 项目联系人电话

    price = scrapy.Field()  # 中标金额
    files = scrapy.Field()  # 文件
    file_urls = scrapy.Field()  # 文件地址
    file_names = scrapy.Field()  # 文件名称
    file_path = scrapy.Field()  # 文件路径

    pass
