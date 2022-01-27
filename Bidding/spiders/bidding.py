import re
import scrapy
import json
from Bidding import items


class BiddingSpider(scrapy.Spider):
    parse_count = 0
    error_count = 0

    name = 'Bidding'
    allowed_domains = ['ggzy.gov.cn']
    start_urls = ['http://deal.ggzy.gov.cn/ds/deal/dealList_find.jsp']

    keywords = ['中央空调', '机房空调', '精密空调', '多联机', '洁净空调', '末端', '新风系统', '通风系统',
                '热泵', '天花机', '风管机', '采暖', '煤改电', '空调']

    # keywords = ['中央空调']

    def start_requests(self):
        for url in self.start_urls:
            form = {'SOURCE_TYPE': '1',  # 来源平台 1-政府采购/工程建设-省平台 2-工程建设-央企招投标
                    'DEAL_TIME': '05',  # 时间范围 05-三月内 04-一月内 03-十天内 02-三天内 01-当天
                    'DEAL_CLASSIFY': '02',  # 业务类型 02-政府采购 01-工程建设
                    'DEAL_STAGE': '0202',  # 信息类型 政府采购-0202-中标结果 工程建设-0104-交易结果公示
                    'DEAL_PROVINCE': '0',  # 来源省 0-不限
                    'DEAL_CITY': '0',  # 来源市 0-不限
                    'DEAL_PLATFORM': '0',  # 具体平台（省） 0-不限
                    'BID_PLATFORM': '0',  # 具体平台（央企招投标） 0-不限
                    'DEAL_TRADE': '0',  # 行业 0-不限
                    'isShowAll': '1',
                    'PAGENUMBER': '1',
                    # 'FINDTXT': self.keywords[0]
                    }
            yield scrapy.FormRequest(url=url, formdata=form, meta={'form': form}, callback=self.parse)

    def parse(self, response, **kwargs):
        text = json.loads(response.text)
        form = response.meta['form']
        # keyword = form['FINDTXT']
        content_url = []
        province = []
        platform = []
        pro_type = []
        pro_name = []
        for each in text['data']:
            each['url'] = each['url'].replace('/a/', '/b/')
            content_url.append(each['url'])
            province.append(each['districtShow'])
            platform.append(each['platformName'])
            pro_type.append(each['classifyShow'])
            pro_name.append(each['title'])

        page_max = text['ttlpage']
        page_current = text['currentpage']
        if page_max and page_current < page_max:
            form['PAGENUMBER'] = str(page_current + 1)
            for i in range(0, len(content_url)):
                # yield scrapy.Request(url=content_url[i], callback=self.parse_content,
                #                      meta={'province': province[i], 'platform': platform[i], 'pro_type': pro_type[i], 'pro_name': pro_name[i], 'keyword': keyword})
                yield scrapy.Request(url=content_url[i], callback=self.parse_purchase_content,
                                     meta={'province': province[i], 'platform': platform[i], 'pro_type': pro_type[i], 'pro_name': pro_name[i]})
            yield scrapy.FormRequest(url=response.url, formdata=form, meta={'form': form}, callback=self.parse)
        # if page_max and page_current == page_max and keyword != self.keywords[-1]:
        #     index = self.keywords.index(keyword)
        #     form['FINDTXT'] = self.keywords[index + 1]
        #     form['PAGENUMBER'] = '1'
        #     yield scrapy.FormRequest(url=response.url, formdata=form, meta={'form': form}, callback=self.parse)

    def parse_purchase_content(self, response):
        self.parse_count += 1
        item = items.BiddingItem()

        content_url = response.url
        # keyword = response.meta['keyword']
        province = response.meta['province']
        platform = response.meta['platform']
        pro_type = response.meta['pro_type']
        pro_name = response.meta['pro_name']
        date = re.findall(r'\d+-\d+-\d+', response.xpath("//div[@class='detail']//p[@class='p_o']/span[contains(text(),'发布时间')]/text()").extract()[0])[0]
        origin_url = response.xpath("//div[@class='detail']//p[@class='p_o']/span[@class='detail_url']/a/@href").extract()[0]
        appendix_url = []
        appendix_name = []
        appendix_path = []

        item['content_url'] = content_url
        # item['keyword'] = keyword
        item['province'] = province
        item['platform'] = platform
        item['pro_type'] = pro_type
        item['pro_name'] = pro_name
        item['date'] = date
        item['origin_url'] = origin_url

        content = []
        all_label = response.xpath("//div[@class='detail_content']//*")
        count = 0
        for each in all_label:
            # '(?<=<)[^\s<>]+(?=>|\s)'----匹配----标签名称如 <p>----p
            if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'tr':
                if count % 2 == 0:
                    for table in each.xpath(".//*"):
                        if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'th' or \
                                re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'td':
                            text = ''.join(table.xpath(".//text()").extract())
                            content.append(text)
                elif count % 2 == 1:
                    for table in each.xpath(".//*"):
                        if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'th' or \
                                re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'td':
                            text = ''.join(table.xpath(".//text()").extract())
                            content.append(text)
                count = count + 1
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'p':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h1':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h2':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h3':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h4':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h5':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'h6':
                text = ''.join(each.xpath(".//text()").extract())
                content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'a':
                href = ''.join(each.xpath("./@href").extract())
                text = ''.join(each.xpath(".//text()").extract())
                content.append(href)
                content.append(text)

            index = []
            for i in range(0, len(content)):
                content[i] = content[i].replace('\t', '').replace('\xa0', '').replace(' ', '')\
                    .replace('\n', '').replace('\u3000', '').replace(',', '').replace('釆', '采').strip()
                if content[i] == '':
                    index.append(i)
            for i in reversed(index):
                del content[i]

        removal = []
        duplicate_index = []
        for i in range(0, len(content)):
            removal.append([content[i]])
        for i in range(0, len(removal)):
            for j in range(i + 1, len(removal)):
                removal[i].append(removal[j][0])
                if len(removal[i]) > 0 and len(removal[i]) % 2 == 0:
                    duplicate = 1
                    for k in range(0, int(len(removal[i]) / 2)):
                        if removal[i][k] != removal[i][k + int(len(removal[i]) / 2)]:
                            duplicate = 0
                            break
                    if duplicate == 1:
                        for k in range(i, i + int(len(removal[i]) / 2)):
                            duplicate_index.append(k)
        for i in reversed(duplicate_index):
            del content[i]

        item['content'] = content

        id_matched = 0
        price_matched = 0
        sup_matched = 0
        pur_matched = 0
        attn_matched = 0
        for i in range(0, len(content)):
            if re.search(r'项目编号', content[i]) and id_matched == 0:
                self.logger.info("项目编号----matched")
                # '[\x00-\xff]+'----匹配----非中文字符，即匹配编号
                # 编号在同一行
                if re.search(r'[\x00-\xff]{5,}', content[i]):
                    # pro_id = content[i].split('：')[-1]
                    pro_id = re.findall(r'[\x00-\xff]{5,}', content[i])[0]
                    item['pro_id'] = pro_id
                # 编号在下一行
                elif re.search(r'[\x00-\xff]{5,}', content[i + 1]):
                    # pro_id = content[i + 1]
                    pro_id = re.findall(r'[\x00-\xff]{5,}', content[i + 1])[0]
                    item['pro_id'] = pro_id
                id_matched = 1
            # '(((中标)(.?成交.?)?)|(成交))金额'----匹配----中标（成交）金额、中标金额、成交金额
            elif re.search(r'(((中标)(.?成交.?)?)|(成交))((金额)|(价格))', content[i]) and price_matched == 0:
                # 金额以万元为单位
                if re.search(r'万元', content[i]):
                    # '(?<=[^\x00-\xff])\d+\.?\d+'----匹配----如 中标金额：1234.00元----1234.00
                    if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i]):
                        self.logger.info("中标金额（万）（同行）----matched")
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i])[0]) * 10000)
                        item['price'] = price
                        # 在金额前后四行搜索
                        for j in range(i - 4, i + 5):
                            if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商名称----matched")
                                sup_name = content[j].split('：')[-1]
                                item['sup_name'] = sup_name
                            elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商地址----matched")
                                sup_add = content[j].split('：')[-1]
                                item['sup_add'] = sup_add
                    elif re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i + 1]):
                        self.logger.info("中标金额（万）（下一行）----matched")
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i + 1])[0]) * 10000)
                        item['price'] = price
                        for j in range(i - 4, i + 5):
                            if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商名称----matched")
                                sup_name = content[j + 1]
                                item['sup_name'] = sup_name
                            elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商地址----matched")
                                sup_add = content[j + 1]
                                item['sup_add'] = sup_add
                    else:
                        self.logger.info("中标金额（万）（表格类）----matched")
                        for j in range(i, len(content)):
                            if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.\d+', content[j]) or re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+.?元', content[j]):
                                price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i])[0]) * 10000)
                                item['price'] = price
                                for k in range(i - 4, i + 5):
                                    if re.search(r'(供应商|中标人).*名称', content[k]) and sup_matched == 0:
                                        self.logger.info("供应商名称----matched")
                                        sup_name = content[j - i + k]
                                        item['sup_name'] = sup_name
                                    elif re.search(r'(供应商|中标人)?.*地址', content[k]) and sup_matched == 0:
                                        self.logger.info("供应商地址----matched")
                                        sup_add = content[j - i + k]
                                        item['sup_add'] = sup_add
                                break
                # 正常金额单位
                else:
                    if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i]):
                        self.logger.info("中标金额（同行）----matched")
                        price = re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i])[0]
                        item['price'] = round(float(price))
                        for j in range(i - 4, i + 5):
                            if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商名称----matched")
                                sup_name = content[j].split('：')[-1]
                                item['sup_name'] = sup_name
                            elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商地址----matched")
                                sup_add = content[j].split('：')[-1]
                                item['sup_add'] = sup_add
                    elif re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i + 1]):
                        self.logger.info("中标金额（下一行）----matched")
                        price = re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[i + 1])[0]
                        item['price'] = round(float(price))
                        for j in range(i - 4, i + 5):
                            if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商名称----matched")
                                sup_name = content[j]
                                item['sup_name'] = sup_name
                            elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_matched == 0:
                                self.logger.info("供应商地址----matched")
                                sup_add = content[j]
                                item['sup_add'] = sup_add
                    else:
                        self.logger.info("中标金额（表格类）----matched")
                        for j in range(i, len(content)):
                            if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.\d+', content[j]) or re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+.?元', content[j]):
                                price = re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+', content[j])[0]
                                item['price'] = round(float(price))
                                for k in range(i - 4, i + 5):
                                    if re.search(r'(供应商|中标人).*名称', content[k]) and sup_matched == 0:
                                        self.logger.info("供应商名称----matched")
                                        sup_name = content[j - i + k]
                                        item['sup_name'] = sup_name
                                    elif re.search(r'(供应商|中标人)?.*地址', content[k]) and sup_matched == 0:
                                        self.logger.info("供应商地址----matched")
                                        sup_add = content[j - i + k]
                                        item['sup_add'] = sup_add
                                break
                sup_matched = 1
                price_matched = 1
            elif re.search(r'(?<=[^\u4e00-\u9fa5])采购人', content[i]) and pur_matched == 0:
                self.logger.info("采购人信息----matched")
                for j in range(i, i + 5):
                    if re.search(r'(名称|单位)：', content[j]):
                        pur_name = content[j].split('：')[-1]
                        item['pur_name'] = pur_name
                    elif re.search(r'地址：', content[j]):
                        pur_add = content[j].split('：')[-1]
                        item['pur_add'] = pur_add
                    elif re.search(r'(联系方式|电话)：', content[j]):
                        pur_tel = content[j].split('：')[-1]
                        item['pur_tel'] = pur_tel
                pur_matched = 1
            elif re.search(r'项目联系方式', content[i]) and attn_matched == 0:
                self.logger.info('项目联系信息----matched')
                for j in range(i, i + 3):
                    if re.search(r'(联系人|名称)：', content[j]):
                        attn_name = content[j].split('：')[-1]
                        item['attn_name'] = attn_name
                    elif re.search(r'电话：', content[j]):
                        attn_tel = content[j].split('：')[-1]
                        item['attn_tel'] = attn_tel
                attn_matched = 1
            elif re.search(r'[a-zA-z]+://[^\s]*', content[i]) and \
                    re.search('(\.txt|\.docx?|\.xlsx?|\.pdf|\.zip|\.rar)$', content[i + 1]):
                self.logger.info('附件----matched')
                appendix_url.append(content[i])

                appendix_name.append(pro_name + '_' + content[i + 1])
                appendix_path.append('=HYPERLINK(%s)' % ('"D://Bidding_Project//total_bidding//appendix//"' + pro_name + '_' + content[i + 1]))

        item['file_urls'] = appendix_url
        item['file_names'] = appendix_name
        item['file_path'] = appendix_path

        yield item

    def parse_bidding_content(self, response):
        item = items.TotalBiddingItem()
        yield item
