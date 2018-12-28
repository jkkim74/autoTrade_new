import telepot
import time
from telepot.loop import MessageLoop


def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == "text":
        user_input = msg["text"]
        if "안녕" in user_input:
            reply = "어 그래"
        else:
            reply = user_input

        bot.sendMessage(chat_id, reply)

token = "398259524:AAHMXMTVrXDfNd-E9tAsA1eRp-u4LopefLI"
#token = ""
bot = telepot.Bot(token)
MessageLoop(bot, handle).run_as_thread()

while 1:
    time.sleep(10)
