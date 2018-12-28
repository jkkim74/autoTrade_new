import telepot
import time
from telepot.loop import MessageLoop
import requests
from bs4 import BeautifulSoup

def get_dividend_earning_rate(code):
    url = "http://finance.naver.com/item/main.nhn?code=" + code
    html = requests.get(url).text
    soup = BeautifulSoup(html, "html5lib")
    tag = soup.select("[id=_dvr]")
    return tag[0].text

def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == "text":
        user_input = msg["text"]
        code = user_input[-6:]

        if '조회' in user_input:
            dividend = get_dividend_earning_rate(code)
            send_msg = "%s 종목의 배당 수익률은 %s%%입니다." % (code, dividend)
            bot.sendMessage(chat_id, send_msg)

#token = "398259524:AAHMXMTVrXDfNd-E9tAsA1eRp-u4LopefLI"
token = ""
bot = telepot.Bot(token)
MessageLoop(bot, handle).run_as_thread()

while 1:
    time.sleep(10)