import pandas as pd
import requests
from bs4 import BeautifulSoup
import util
import requests
code = '078520'#'115570'
page = 1
bad_news_cnt = 0
while True:
    if page == 5:
        break
    req = requests.get('https://finance.naver.com/item/news_news.nhn?code='+code+'&page='+str(page)+'&sm=title_entity_id.basic&clusterId=')#naver
    #req=requests.get('https://coinmarketcap.com/currencies/bitcoin/historical-data/?start=20130428&end=20180124')
    #req = requests.get('http://finance.daum.net/quotes/A041140#news/stock')#daum
    html = req.text
    #print(html)
    soup = BeautifulSoup(html, 'html.parser')
    columns=soup.select('div.tb_cont > table > thead > tr > th')
    #print(columns)

    contents = soup.select('div.tb_cont > table > tbody > tr')
    dfcontent = []
    alldfcontents = []
    article_id_list = []
    for content in contents:
        str_date = content.find("td", {"class":"date"}).text
        # print(str_date)
        for link  in content.find_all("a"):
            if 'href' in link.attrs:
                str_href = link.attrs['href']
                if 'news_read.nhn' in str_href:
                    #print(str_href)
                    article_id_loc = str_href.find('article_id=') + 11
                    #print(str_href[article_id_loc:41])
                    article_id = str_href[article_id_loc:41]
                    office_id = str_href[52:55]
                    article_id_list.append((article_id, office_id, str_date))
                    #print(article_id_loc)

    #print(alldfcontents)

    for article_id, office_id, str_date in article_id_list:
        req_detail = requests.get('https://finance.naver.com/item/news_read.nhn?article_id='+article_id+'&office_id='+office_id+'&code='+code+'&page=&sm=title_entity_id.basic')
        html_view = req_detail.text
        soup_view = BeautifulSoup(html_view, 'html.parser')
        contents_view = soup_view.find("div", {"id": "news_read"}).text
        # if contents_view.find('영업이익') > -1 and contents_view.find('상승') > -1:
        #     print(str_date)
        #     print(contents_view)

        # 시가갭 당일에 조건검색
        prev_bus_day_0 = util.get_prev_date(0, 1)
        prev_bus_day_1 = util.get_prev_date(2, 3)
        prev_bus_day_list = prev_bus_day_0 + prev_bus_day_1
        result = []
        for prev_bus_day in prev_bus_day_list:
            result.append(prev_bus_day.replace('-', ''))
        article_date = str_date[:11].replace('.', '').replace(' ','')

        #print(article_date, result)
        if article_date in result:
            print(article_date)
            print(contents_view)
            if contents_view.find('유상증자') > -1 \
               or (contents_view.find('조회공시') > -1 and contents_view.find('요구') and contents_view.find('공시대상') and (contents_view.find('없다') or contents_view.find('없어'))):
                bad_news_cnt +=1
    page += 1
print('악재 : ', bad_news_cnt)