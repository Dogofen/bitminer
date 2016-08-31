import signal
import tradehandler
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from time import sleep
from matplotlib import style
import matplotlib as mpl
import ema
majorFormatter = mpl.dates.DateFormatter('%H:%M:%S')

style.use('fivethirtyeight')
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
h = tradehandler.TradeHandler('eth_usd', "key.txt")
h.start()
sleep(5)


def animate(i):
    try:
        ax1.clear()
        em = ema.ema(h.bidHistory['price'])
        ax1.plot(h.bidHistory['time'], h.bidHistory['price'], '-o',
                 label='second')
        ax1.plot(h.bidHistory['time'], em, '-o',
                 label='third')
        ax1.xaxis.set_major_formatter(majorFormatter)
        ax1.autoscale_view()
    except:
        pass

ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.legend()
plt.show()
h.stop()
print "End of the program. I was killed gracefully :)"


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True
