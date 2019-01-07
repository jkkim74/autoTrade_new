import pandas as pd
import requests
from bs4 import BeautifulSoup

req = requests.get('https://finance.naver.com/item/news_news.nhn?code=041140&page=&sm=title_entity_id.basic&clusterId=')#naver
#req=requests.get('https://coinmarketcap.com/currencies/bitcoin/historical-data/?start=20130428&end=20180124')
#req = requests.get('http://finance.daum.net/quotes/A041140#news/stock')#daum
html = req.text
#print(html)
soup = BeautifulSoup(html, 'html.parser')
columns=soup.select('div.tb_cont > table > thead > tr > th')
print(columns)

contents = soup.select('div.tb_cont > table > tbody > tr')
dfcontent = []
alldfcontents = []

for content in contents:
    tds = content.find_all("td")
    for td in tds:
        dfcontent.append(td.text)
    alldfcontents.append(dfcontent)
    dfcontent=[]

print(alldfcontents)

req_detail = requests.get('https://finance.naver.com/item/news_read.nhn?article_id=0003479311&office_id=011&code=041140&page=&sm=title_entity_id.basic')
html_view = req_detail.text
print(html_view)
soup_view = BeautifulSoup(html_view, 'html.parser')
contents_view = soup_view.find("div", {"id": "news_read"})
print(contents_view)