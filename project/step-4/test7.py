import time
import datetime as dt
import urllib.request
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.animation as Animation
from matplotlib import style
import matplotlib
import threading

style.use('fivethirtyeight')

INTERVAL = 5 # seconds to sleep between data update calls

#global variables to hold the data
xdata = []
ydata = []

def usd_in_bitcoin():
    try:
        resp = urllib.request.urlopen("https://bitcoinwisdom.com/")
    except Exception as e:
        print(e)
    text = resp.read()
    soup = BeautifulSoup(text, 'html.parser')
    intermediate = soup.find('tr', {"id": "o_btcusd"})
    ans = intermediate.find('td', {'class': 'r'})
    return ans.contents[0]

def monitor_bitcoin():
    '''runs continuously and updates the global xdata and ydata lists'''
    while True:
        curr_value = float(usd_in_bitcoin())
        xdata.append(dt.datetime.now())
        ydata.append(curr_value)
        time.sleep(INTERVAL)

def animate(i):
    # update the data
    line.set_data(xdata, ydata)

    # update the scales to fit:
    if ydata:
        ax.set_ylim(min(ydata), max(ydata))
    if xdata:
        ax.set_xlim(min(xdata), max(xdata))

    return line,

def plotting():
    global ax, line
    fig = plt.figure()
    ax = fig.add_subplot(111)
    line, = ax.plot([], [], lw=2) # initial empty graph
    ani = Animation.FuncAnimation(fig, animate, interval=1000)
    plt.show() # start animation loop

def main():
    a = threading.Thread(target=monitor_bitcoin)
    a.daemon = True # this makes the child quit when the main thread quits
    a.start()
    print("thread name ==>", a.getName())
    b = threading.Thread(target=monitor_bitcoin)
    b.daemon = True # this makes the child quit when the main thread quits
    b.start()
    print("thread name ==>", b.getName())
    plotting()

if __name__ == '__main__':
    main()