# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import pymongo
import logging
from scrapy import Request
from Bidding import settings
from scrapy.pipelines.files import FilesPipeline


class BiddingPipeline:

    def __init__(self):
        self.store_count = 0
        self.duplicate_count = 0
        self.error_count = 0

        host = settings.MONGODB_HOST
        port = settings.MONGODB_PORT
        db_name = settings.MONGODB_DBNAME
        sheet_name = settings.MONGODB_SHEETNAME

        client = pymongo.MongoClient(host=host, port=port)
        db = client[db_name]
        self.sheet = db[sheet_name]

    def process_item(self, item, spider):
        data = dict(item)
        if data['content'] and self.store_count == 0:
            self.sheet.insert_one(data)
            self.store_count += 1
            return item
        elif self.store_count != 0 and not self.sheet.find_one({'pro_id': data['pro_id']}) and data['content']:
            self.sheet.insert_one(data)
            self.store_count += 1
            return item
        elif self.store_count != 0 and self.sheet.find_one({'pro_id': data['pro_id']}):
            self.duplicate_count += 1

        logging.info('Current Storage Counted ---- ' + str(self.store_count))
        logging.info('Current Duplicated Counted ----- ' + str(self.duplicate_count))
        # cd C://Program Files//MongoDB//Server//4.4//bin
        # mongoexport -d bidding -c total_bidding -f classify,stage,keyword,date,platform,province,content_url,origin_url,pro_name,pro_id,pur_name,pur_add,pur_tel,attn_name,attn_tel,sup_name,sup_add,price,period,content,file_path --type=csv -o D:/Bidding/output.csv


class FileDownloadPipeline(FilesPipeline):

    def get_media_requests(self, item, info):
        urls = ItemAdapter(item).get(self.files_urls_field, [])
        names = ItemAdapter(item).get(self.files_names_field, [])
        for i in range(0, len(urls)):
            return [Request(url=urls[i], meta={'name': names[i]})]

    def file_path(self, request, response=None, info=None, *, item=None):
        return '%s' % request.meta['name']
