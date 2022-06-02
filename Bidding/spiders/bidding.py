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

    keywords = ['机房空调', '精密空调', '多联机', '多联式空调', '洁净空调', '末端', '新风系统', '新风机', '通风系统', '通风空调', '离心机', '螺杆机',
                '热泵', '天花机', '风管机', '风管送风式空调', '采暖', '煤改电', '烘干机', '中央空调', '空调']

    # keywords = ['中央空调']

    def start_requests(self):
        for url in self.start_urls:
            # form = {'SOURCE_TYPE': '1',  # 来源平台 1-政府采购/工程建设-省平台 2-工程建设-央企招投标
            #         'DEAL_TIME': '05',  # 时间范围 05-三月内 04-一月内 03-十天内 02-三天内 01-当天
            #         'DEAL_CLASSIFY': '01',  # 业务类型 02-政府采购 01-工程建设
            #         'DEAL_STAGE': '0104',  # 信息类型 政府采购-0202-中标结果 工程建设-0104-交易结果公示
            #         'DEAL_PROVINCE': '0',  # 来源省 0-不限
            #         'DEAL_CITY': '0',  # 来源市 0-不限
            #         'DEAL_PLATFORM': '0',  # 具体平台（省） 0-不限
            #         'BID_PLATFORM': '0',  # 具体平台（央企招投标） 0-不限
            #         'DEAL_TRADE': '0',  # 行业 0-不限
            #         'isShowAll': '1',
            #         'PAGENUMBER': '1',
            #         'FINDTXT': self.keywords[0]
            #         }
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
                    'FINDTXT': self.keywords[0]
                    }
            yield scrapy.FormRequest(url=url, formdata=form, meta={'form': form}, callback=self.parse)

    def parse(self, response, **kwargs):
        self.logger.info('From <parse> ---- Executing function <parse>')

        text = json.loads(response.text)
        form = response.meta['form']
        keyword = form['FINDTXT']
        content_url = []
        province = []
        platform = []
        classify = []
        stage = []
        pro_name = []
        for each in text['data']:
            each['url'] = each['url']
            content_url.append(each['url'])
            province.append(each['districtShow'])
            platform.append(each['platformName'])
            classify.append(each['classifyShow'])
            stage.append(each['stageShow'])
            pro_name.append(each['title'])

        self.logger.info('From <parse> ---- Keyword maintenant: ' + keyword)

        page_max = text['ttlpage']
        page_current = text['currentpage']

        self.logger.info('From <parse> ---- Page Current: ' + str(page_current))
        self.logger.info('From <parse> ---- Page Max:' + str(page_max))

        if page_max and page_current < page_max:
            form['PAGENUMBER'] = str(page_current + 1)
            for i in range(0, len(content_url)):
                yield scrapy.Request(url=content_url[i], callback=self.parse_pro_id,
                                     meta={'form': form, 'province': province[i], 'platform': platform[i], 'classify': classify[i], 'stage': stage[i], 'pro_name': pro_name[i], 'keyword': keyword})
                self.logger.info('From <parse> ---- Calling back to function <parse_pro_id> with keyword: ' + keyword)
            yield scrapy.FormRequest(url=response.url, formdata=form, meta={'form': form}, callback=self.parse)
            self.logger.info('From <parse> ---- Calling back to function <parse> with a new page number: ' + form['PAGENUMBER'])
        # 切换关键字搜索
        if page_max and page_current == page_max and keyword != self.keywords[-1]:
            index = self.keywords.index(keyword)
            form['FINDTXT'] = self.keywords[index + 1]
            form['PAGENUMBER'] = '1'
            yield scrapy.FormRequest(url=response.url, formdata=form, meta={'form': form}, callback=self.parse)
            self.logger.info('From <parse> ---- Calling back to function <parse> with a new keyword: ' + form['FINDTXT'])
        # 切换业务类型
        if page_max and page_current == page_max and keyword == self.keywords[-1] and form['DEAL_CLASSIFY'] == '02':
            form['FINDTXT'] = self.keywords[0]
            form['PAGENUMBER'] = '1'
            form['DEAL_CLASSIFY'] = '01'
            form['DEAL_STAGE'] = '0104'
            yield scrapy.FormRequest(url=response.url, formdata=form, meta={'form': form}, callback=self.parse)
            self.logger.info('From <parse> ---- Calling back to function <parse> with 政府采购 switching to 工程建设')

    def parse_pro_id(self, response):
        self.logger.info('From <parse_pro_id> ---- Executing function <parse_pro_id>')

        form = response.meta['form']
        province = response.meta['province']
        platform = response.meta['platform']
        classify = response.meta['classify']
        stage = response.meta['stage']
        pro_name = response.meta['pro_name']
        keyword = response.meta['keyword']

        content_url = response.url.replace('/a/', '/b/')
        pro_id = response.xpath("//div[@class='fully']/p[@class='p_o']/span/text()").extract()[0].split('：')[-1]

        self.logger.info('From <parse_pro_id> ---- Deal classify maintenant: ' + classify + ' Classify number: ' + form['DEAL_CLASSIFY'])

        if classify == '政府采购':
            yield scrapy.Request(url=content_url, callback=self.parse_purchase_content,
                                 meta={'form': form, 'province': province, 'platform': platform, 'classify': classify, 'stage': stage, 'pro_name': pro_name, 'pro_id': pro_id, 'keyword': keyword})
            self.logger.info('From <parse_pro_id> ---- Calling back to function <parse_purchase_content> with project: ' + pro_name)
        elif classify == '工程建设':
            yield scrapy.Request(url=content_url, callback=self.parse_bidding_content,
                                 meta={'form': form, 'province': province, 'platform': platform, 'classify': classify, 'stage': stage, 'pro_name': pro_name, 'pro_id': pro_id, 'keyword': keyword})
            self.logger.info('From <parse_pro_id> ---- Calling back to function <parse_bidding_content> with project: ' + pro_name)

    def parse_purchase_content(self, response):
        self.logger.info('From <parse_purchase_content> ---- Executing function <parse_purchase_content>')

        self.parse_count += 1
        item = items.BiddingItem()

        content_url = response.url
        keyword = response.meta['keyword']
        province = response.meta['province']
        platform = response.meta['platform']
        classify = response.meta['classify']
        stage = response.meta['stage']
        pro_name = response.meta['pro_name']
        pro_id = response.meta['pro_id']
        date = re.findall(r'\d+-\d+-\d+', response.xpath("//div[@class='detail']//p[@class='p_o']/span[contains(text(),'发布时间')]/text()").extract()[0])[0]
        origin_url = response.xpath("//div[@class='detail']//p[@class='p_o']/span[@class='detail_url']/a/@href").extract()[0]
        appendix_url = []
        appendix_name = []
        appendix_path = []

        item['content_url'] = content_url
        item['keyword'] = keyword
        item['province'] = province
        item['platform'] = platform
        item['classify'] = classify
        item['stage'] = stage
        item['pro_name'] = pro_name
        item['pro_id'] = pro_id
        item['date'] = date
        item['origin_url'] = origin_url

        content = []
        all_label = response.xpath("//div[@class='detail_content']//*")
        for each in all_label:
            # '(?<=<)[^\s<>]+(?=>|\s)'----匹配----标签名称如 <p>----p
            duplicated = 0
            if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'th':
                for table in each.xpath(".//*"):
                    if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'p' or \
                            re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'div':
                        duplicated = 1
                if duplicated == 0:
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'td':
                for table in each.xpath(".//*"):
                    if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'p' or \
                            re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'div':
                        duplicated = 1
                if duplicated == 0:
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'div':
                if not each.xpath(".//*") and each.xpath("./text()"):
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
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
                content[i] = content[i].replace('\t', '').replace('\xa0', '').replace(' ', '').replace('&nbsp', '') \
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

        price = '-'
        price_matched = 0
        sup_name_matched = 0
        sup_add_matched = 0
        pur_name_matched = 0
        pur_add_matched = 0
        pur_tel_matched = 0
        attn_name_matched = 0
        attn_tel_matched = 0
        for i in range(0, len(content)):
            # '(((中标)(.?成交.?)?)|(成交))金额'----匹配----中标（成交）金额、中标金额、成交金额
            if re.search(r'((中标(（成交）)?|成交|投标|总)[\u4e00-\u9fa5]*?(金额|价|总价|报价|价格))(?![\u4e00-\u9fa5])', content[i]) and price_matched == 0:
                self.logger.info('From <parse_purchase_content> ---- 中标金额 ---- Matched')
                if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i]):
                    self.logger.info('From <parse_purchase_content> ---- 金额数字串 ---- same row ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]))
                    if re.search(r'万元', content[i]):
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]) * 10000)
                        item['price'] = price
                        price_matched = 1
                    else:
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]))
                        item['price'] = price
                        price_matched = 1
                    # 在金额前后四行搜索
                    for j in (0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 5 else i + 5):
                        if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_name_matched == 0:
                            self.logger.info("From <parse_purchase_content> ---- 供应商名称 ---- Matched")
                            sup_name = content[j].split('：')[-1]
                            item['sup_name'] = sup_name
                            sup_name_matched = 1
                        elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_add_matched == 0:
                            self.logger.info("From <parse_purchase_content> ---- 供应商地址 ---- Matched")
                            sup_add = content[j].split('：')[-1]
                            item['sup_add'] = sup_add
                            sup_add_matched = 1
                        if sup_name_matched == 1 and sup_add_matched == 1:
                            break
                elif re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1]):
                    self.logger.info('From <parse_purchase_content> ---- 金额数字串 ---- next row ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]))
                    if re.search(r'万元', content[i + 1]):
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]) * 10000)
                        item['price'] = price
                        price_matched = 1
                    else:
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]))
                        item['price'] = price
                        price_matched = 1
                    for j in (0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 5 else i + 5):
                        if re.search(r'(供应商|中标人).*名称[^地址金额]*', content[j]) and sup_name_matched == 0:
                            self.logger.info("From <parse_purchase_content> ---- 供应商名称 ---- Matched")
                            sup_name = content[j].split('：')[-1]
                            item['sup_name'] = sup_name
                            sup_name_matched = 1
                        elif re.search(r'(供应商|中标人).*地址[^名称金额]*', content[j]) and sup_add_matched == 0:
                            self.logger.info("From <parse_purchase_content> ---- 供应商地址 ---- Matched")
                            sup_add = content[j].split('：')[-1]
                            item['sup_add'] = sup_add
                            sup_add_matched = 1
                        if sup_name_matched == 1 and sup_add_matched == 1:
                            break
                else:
                    for j in range(i, len(content)):
                        if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j]):
                            self.logger.info('From <parse_purchase_content> ---- 金额数字串 ---- table ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]))
                            if re.search(r'万元', content[i]) or re.search(r'万元', content[j]):
                                price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]) * 10000)
                                item['price'] = price
                                price_matched = 1
                            else:
                                price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]))
                                item['price'] = price
                                price_matched = 1
                            for k in (0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 5 else i + 5):
                                if re.search(r'(供应商|中标人).*名称', content[k]) and sup_name_matched == 0:
                                    self.logger.info("From <parse_purchase_content> ---- 供应商名称 ---- Matched")
                                    sup_name = content[j - i + k]
                                    item['sup_name'] = sup_name
                                    sup_name_matched = 1
                                elif re.search(r'(供应商|中标人)?.*地址', content[k]) and sup_add_matched == 0:
                                    self.logger.info("From <parse_purchase_content> ---- 供应商地址 ---- Matched")
                                    sup_add = content[j - i + k]
                                    item['sup_add'] = sup_add
                                    sup_add_matched = 1
                                if sup_name_matched == 1 and sup_add_matched == 1:
                                    break
                            if price_matched == 1:
                                break
            elif re.search(r'(?<=[^\u4e00-\u9fa5])采购人', content[i]) and pur_name_matched == 0 and pur_add_matched == 0 and pur_tel_matched == 0:
                self.logger.info("From <parse_purchase_content> ---- 采购人信息 ---- Matched")
                for j in range(i, len(content) - 1 if len(content) - i <= 5 else i + 5):
                    if re.search(r'(名称|单位)：', content[j]):
                        pur_name = content[j].split('：')[-1]
                        item['pur_name'] = pur_name
                        pur_name_matched = 1
                    elif re.search(r'地址：', content[j]):
                        pur_add = content[j].split('：')[-1]
                        item['pur_add'] = pur_add
                        pur_add_matched = 1
                    elif re.search(r'(联系方式|电话)：', content[j]):
                        pur_tel = content[j].split('：')[-1]
                        item['pur_tel'] = pur_tel
                        pur_tel_matched = 1
                if pur_name_matched == 1 and pur_add_matched == 1 and pur_tel_matched == 1:
                    break
            elif re.search(r'项目联系方式', content[i]) and attn_name_matched == 0 and attn_tel_matched == 0:
                self.logger.info('From <parse_purchase_content> ---- 项目联系信息 ---- Matched')
                for j in range(i, len(content) - 1 if len(content) - i <= 3 else i + 3):
                    if re.search(r'(联系人|名称)：', content[j]):
                        attn_name = content[j].split('：')[-1]
                        item['attn_name'] = attn_name
                        attn_name_matched = 1
                    elif re.search(r'电话：', content[j]):
                        attn_tel = content[j].split('：')[-1]
                        item['attn_tel'] = attn_tel
                        attn_tel_matched = 1
                    if attn_name_matched == 1 and attn_tel_matched == 1:
                        break
            elif re.search(r'[a-zA-z]+://[^\s]*', content[i]) and \
                    re.search('(\.txt|\.docx?|\.xlsx?|\.pdf|\.zip|\.rar)$', content[i + 1]):
                self.logger.info('From <parse_purchase_content> ---- 附件 ---- Matched')
                appendix_url.append(content[i])

                appendix_name.append(pro_name + '_' + content[i + 1])
                appendix_path.append('=HYPERLINK(%s)' % ('"D://Bidding//appendix//"' + pro_name + '_' + content[i + 1]))

        item['file_urls'] = appendix_url
        item['file_names'] = appendix_name
        item['file_path'] = appendix_path

        self.logger.info('---------------------------------------- RESULT ----------------------------------------')
        self.logger.info('From <parse_purchase_content> ---- 招标类型 ---- ' + classify)
        self.logger.info('From <parse_purchase_content> ---- 项目名称 ---- ' + pro_name)
        self.logger.info('From <parse_purchase_content> ---- 中标金额 ---- ' + str(price))
        self.logger.info('From <parse_purchase_content> ---- URL ---- ' + content_url)

        yield item

    def parse_bidding_content(self, response):
        self.logger.info('From <parse_bidding_content> ---- Executing function <parse_bidding_content>')
        self.parse_count += 1
        item = items.BiddingItem()

        content_url = response.url
        keyword = response.meta['keyword']
        province = response.meta['province']
        platform = response.meta['platform']
        classify = response.meta['classify']
        stage = response.meta['stage']
        pro_name = response.meta['pro_name']
        pro_id = response.meta['pro_id']
        date = re.findall(r'\d+-\d+-\d+', response.xpath("//div[@class='detail']//p[@class='p_o']/span[contains(text(),'发布时间')]/text()").extract()[0])[0]
        origin_url = response.xpath("//div[@class='detail']//p[@class='p_o']/span[@class='detail_url']/a/@href").extract()[0]

        item['content_url'] = content_url
        item['keyword'] = keyword
        item['province'] = province
        item['platform'] = platform
        item['classify'] = classify
        item['stage'] = stage
        item['pro_name'] = pro_name
        item['pro_id'] = pro_id
        item['date'] = date
        item['origin_url'] = origin_url

        content = []
        all_label = response.xpath("//div[@class='detail_content']//*")
        for each in all_label:
            # '(?<=<)[^\s<>]+(?=>|\s)'----匹配----标签名称如 <p>----p
            duplicated = 0
            if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'th':
                for table in each.xpath(".//*"):
                    if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'p' or \
                            re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'div':
                        duplicated = 1
                if duplicated == 0:
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'td':
                for table in each.xpath(".//*"):
                    if re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'p' or \
                            re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', table.get())[0] == 'div':
                        duplicated = 1
                if duplicated == 0:
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
            elif re.findall(r'(?<=<)[^\s<>]+(?=>|\s)', each.get())[0] == 'div':
                if not each.xpath(".//*") and each.xpath("./text()"):
                    text = ''.join(each.xpath(".//text()").extract())
                    content.append(text)
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
                content[i] = content[i].replace('\t', '').replace('\xa0', '').replace(' ', '').replace('&nbsp', '') \
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

        price = '-'
        price_matched = 0
        sup_matched = 0
        pur_matched = 0
        period_matched = 0

        for i in range(0, len(content)):
            if content[i] == '评标排序':
                self.logger.info('From <parse_bidding_content> ---- 评标排序 ---- Matched')
                for j in range(i, len(content)):
                    if re.search(r'((中标(（成交）)?|成交|投标|总)[\u4e00-\u9fa5]*?(金额|价|总价|报价|价格))(?![\u4e00-\u9fa5])', content[j]) and price_matched == 0:
                        self.logger.info('From <parse_bidding_content> ---- 中标金额 ---- Matched')
                        for k in range(j, len(content)):
                            if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[k]):
                                self.logger.info('From <parse_bidding_content> ---- 金额数字串 ---- table ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[k])[0]))
                                if re.search(r'万元', content[j]) or re.search(r'万元', content[k]):
                                    price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[k])[0]) * 10000)
                                    item['price'] = price
                                    price_matched = 1
                                else:
                                    price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[k])[0]))
                                    item['price'] = price
                                    price_matched = 1
                                for l in (0 if j <= 4 else j - 4, len(content) - 1 if len(content) - j <= 5 else j + 5):
                                    if re.search(r'名称|(中标[\u4e00-\u9fa5]*人|单位)(?![\u4e00-\u9fa5])', content[l]) and sup_matched == 0 and len(content[j]) <= 10:
                                        self.logger.info("中标单位名称----matched")
                                        sup_name = content[k - j + l]
                                        item['sup_name'] = sup_name
                                        sup_matched = 1
                                    elif re.search(r'工期', content[l]) and period_matched == 0 and len(content[l]) <= 10:
                                        self.logger.info("工期----matched")
                                        period = re.findall(r'(?<![\d.\-\u4e00-\u9fa5])\d{2,3}(?![\d.])', content[k - j + l])[0]
                                        item['period'] = period
                                        period_matched = 1
                                if price_matched == 1:
                                    break
            if re.search(r'((中标(（成交）)?|成交|投标|总)[\u4e00-\u9fa5]*?(金额|价|总价|报价|价格))(?![\u4e00-\u9fa5])', content[i]) and price_matched == 0 and len(re.findall(r'[\u4e00-\u9fa5]*', content[i])[0]) <= 12:
                self.logger.info('From <parse_bidding_content> ---- 中标金额 ---- Matched')
                if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i]):
                    self.logger.info('From <parse_bidding_content> ---- 金额数字串 ---- same row ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]))
                    if re.search(r'万元', content[i]):
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]) * 10000)
                        item['price'] = price
                        price_matched = 1
                    else:
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i])[0]))
                        item['price'] = price
                        price_matched = 1
                    for j in range(0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 5 else i + 5):
                        if re.search(r'名称|(中标[\u4e00-\u9fa5]*人|单位)(?![\u4e00-\u9fa5])', content[j]) and sup_matched == 0 and len(content[i]) <= 10:
                            self.logger.info("From <parse_bidding_content> ---- 中标单位名称 ---- Matched")
                            sup_name = content[j].split('：')[-1]
                            item['sup_name'] = sup_name
                            sup_matched = 1
                        elif re.search(r'工期', content[j]) and period_matched == 0 and len(content[j]) <= 10:
                            self.logger.info("From <parse_bidding_content> ---- 工期 ---- Matched")
                            period = re.findall(r'(?<![\d.\-\u4e00-\u9fa5])\d{2,3}(?![\d.])', content[j])[0]
                            item['period'] = period
                            period_matched = 1
                elif re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1]):
                    self.logger.info('From <parse_bidding_content> ---- 金额数字串 ---- next row ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]))
                    if re.search(r'万元', content[i]) or re.search(r'万元', content[i + 1]):
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]) * 10000)
                        item['price'] = price
                        price_matched = 1
                    else:
                        price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[i + 1])[0]))
                        item['price'] = price
                        price_matched = 1
                    for j in (0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 9 else i + 9):
                        if re.search(r'名称|(中标[\u4e00-\u9fa5]*人|单位)(?![\u4e00-\u9fa5])', content[j]) and sup_matched == 0 and len(content[i]) <= 10:
                            self.logger.info("From <parse_bidding_content> ---- 中标单位名称 ---- Matched")
                            sup_name = content[j + 1].split('：')[-1]
                            item['sup_name'] = sup_name
                            sup_matched = 1
                        elif re.search(r'工期', content[j]) and period_matched == 0 and len(content[j]) <= 10:
                            self.logger.info("From <parse_bidding_content> ---- 工期 ---- Matched")
                            period = re.findall(r'(?<![\d.\-\u4e00-\u9fa5])\d{2,3}(?![\d.])', content[j + 1])[0]
                            item['period'] = period
                            period_matched = 1
                else:
                    for j in range(i, len(content)):
                        if re.search(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j]):
                            self.logger.info('From <parse_bidding_content> ---- 金额数字串 ---- table ---- Matched: ' + str(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]))
                            if re.search(r'万元', content[i]) or re.search(r'万元', content[j]):
                                price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]) * 10000)
                                item['price'] = price
                                price_matched = 1
                            else:
                                price = round(float(re.findall(r'(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+(?=\(?（?万?元|）)|(?<![\u4e00-\u9fa5a-zA-Z])\d+\.?\d+$', content[j])[0]))
                                item['price'] = price
                                price_matched = 1
                            for k in (0 if i <= 4 else i - 4, len(content) - 1 if len(content) - i <= 5 else i + 5):
                                if re.search(r'名称|(中标[\u4e00-\u9fa5]*人|单位)(?![\u4e00-\u9fa5])', content[k]) and sup_matched == 0 and len(content[i]) <= 10:
                                    self.logger.info("From <parse_bidding_content> ---- 中标单位名称 ---- Matched")
                                    sup_name = content[j - i + k]
                                    item['sup_name'] = sup_name
                                    sup_matched = 1
                                elif re.search(r'工期', content[k]) and period_matched == 0 and len(content[k]) <= 10:
                                    self.logger.info("From <parse_bidding_content> ---- 工期 ---- Matched")
                                    period = re.findall(r'(?<![\d.\-\u4e00-\u9fa5])\d{2,3}(?![\d.])', content[j - i + k])[0]
                                    item['period'] = period
                                    period_matched = 1
                            if price_matched == 1:
                                break
            elif re.search(r'招标人(?![\u4e00-\u9fa5])|招标人名称|建设单位(名称)?', content[i]) and pur_matched == 0 and len(content[i]) <= 12:
                self.logger.info("From <parse_bidding_content> ---- 招标单位名称 ---- Matched")
                if '：' in content[i]:
                    if re.search(r'[\u4e00-\u9fa5]+', content[i].split('：')[-1]):
                        pur_name = content[i].split('：')[-1]
                        item['pur_name'] = pur_name
                        pur_matched = 1
                    elif not re.search(r'[\u4e00-\u9fa5]+', content[i].split('：')[-1]):
                        pur_name = content[i + 1]
                        item['pur_name'] = pur_name
                        pur_matched = 1
                elif '：' not in content[i]:
                    pur_name = content[i + 1]
                    item['pur_name'] = pur_name
                    pur_matched = 1
            elif re.search(r'招标人信息', content[i]) and content[i + 1] == '名称' and pur_matched == 0:
                pur_name = content[i + 2]
                item['pur_name'] = pur_name
                pur_matched = 1
            elif re.search(r'中标人信息', content[i]) and content[i + 1] == '名称' and sup_matched == 0:
                sup_name = content[i + 2]
                item['sup_name'] = sup_name
                sup_matched = 1

        self.logger.info('---------------------------------------- RESULT ----------------------------------------')
        self.logger.info('From <parse_bidding_content> ---- 招标类型 ---- ' + classify)
        self.logger.info('From <parse_bidding_content> ---- 项目名称 ---- ' + pro_name)
        self.logger.info('From <parse_bidding_content> ---- 中标金额 ---- ' + str(price))
        self.logger.info('From <parse_bidding_content> ---- URL ---- ' + content_url)

        yield item
