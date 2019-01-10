import pandas as pd
import requests
from bs4 import BeautifulSoup
code = '068290'
req = requests.get('https://finance.naver.com/item/news_news.nhn?code='+code+'&page=2&sm=title_entity_id.basic&clusterId=')#naver
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
    if contents_view.find('영업이익') > -1 and contents_view.find('상승') > -1:
        print(str_date)
        print(contents_view)


