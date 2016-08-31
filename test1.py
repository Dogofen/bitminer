import signal
import numpy
import btceapi

key_file = 'key.txt'
pair = "btc_usd"
handler = btceapi.KeyHandler(key_file)
key = handler.getKeys()[0]
print "Trading with key %s" % key


def _attemptBuy(price):
    conn = btceapi.BTCEConnection()
    try:
        info = api.getInfo(conn)
        # Limit order to what we can afford to buy.
        available = float(getattr(info, "balance_usd"))
        buy_amount = available / price
        print "attempting to buy %s bitcoin at %s for %s" % (
            buy_amount, price, buy_amount*price
        )
        r = api.trade(pair, "buy", price, buy_amount, conn)
        # If the order didn't fill completely, cancel the remaining order
        if r.order_id != 0:
            print "\tCanceling unfilled portion of order"
            api.cancelOrder(r.order_id, conn)
            conn.close()
            raise Exception('buy failure')
    except:
        print "error buying"
        conn.close()
        raise Exception('buy failure')
        pass

    print "\tReceived %s bits" % (r.received)
    conn.close()


def _attemptSell(price):
    conn = btceapi.BTCEConnection()
    try:
        info = api.getInfo(conn)
        # Limit order to what we have available to sell.
        available = float(getattr(info, "balance_btc"))
        r = api.trade(pair, "sell", price, available, conn)
        # If the order didn't fill completely, cancel the remaining order
        if r.order_id != 0:
            print "\tCanceling unfilled portion of order"
            api.cancelOrder(r.order_id, conn)
            conn.close()
            raise Exception('sell failure')
    except:
        "print sell failed"
        conn.close()
        raise Exception('sell failure')
    print "\tSold %s at %s" % (r.received, price)
    conn.close()
# This overrides the onNewDepth method in the TraderBase class, so the
# framework will automatically pick it up and send updates to it.


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

import pudb
pudb.set_trace()
conn = btceapi.BTCEConnection()
api = btceapi.TradeAPI(key, handler)
available = getattr(api.getInfo(conn), "balance_usd")
killer = GracefulKiller()
mean = 600
counter = 0
sample_rate = 30
DeltaList = [0]*sample_rate
buy_flag = False
delta = 0
adjust = 0.99999
conn.close()
while True:
    ask_list = []
    price_list = []
    if counter == sample_rate:
        counter = 0
        print "counter has zeroed"
        print "delta list is: %s" % DeltaList
    try:
        conn = btceapi.BTCEConnection()
        tradeHistory = btceapi.getTradeHistory(pair, conn)
        available = getattr(api.getInfo(conn), "balance_usd")
        asks, bids = btceapi.getDepth("btc_usd", conn)
        for ask in asks:
            ask_list.append(ask[0])
        for i in range(int(1.5*sample_rate)):
            price_list.append(tradeHistory[i].price)
        last_mean = mean
        mean = numpy.mean(ask_list)
    except:
        print "error getDepth"
        pass
    conn.close()
    try:
        DeltaList[counter] = float(mean-last_mean)
        filtered_delta = filter(lambda x: x != 0, DeltaList)
        delta = numpy.mean(filtered_delta)
    except:
        print "error"
        pass
    if delta > 0.03 and available > 100:
        try:
            price = float(ask_list[0])
            print "attempting buying at delta: %s for price %s and list %s" % (
                delta, price, DeltaList
            )
            _attemptBuy(price)
            buy_flag = True
        except:
            try:
                price = price*(2-adjust)
                print "attempting buying at delta: %s for price %s and list %s" % (
                    delta, price, DeltaList
                )
                _attemptBuy(price)
                buy_flag = True
            except:
                try:
                    price = price*(2-adjust)
                    print "attempting buying at delta: %s for price %s and list %s" % (
                        delta, price, DeltaList
                    )
                    _attemptBuy(price)
                    buy_flag = True
                except:
                    print "buy failed"
                    pass
    elif available < 100 and delta < -0.01:
        try:
            DeltaList[counter] = DeltaList[counter]*(2-adjust)
            if bids[0][0] > 500:
                price = float(ask_list[0])
                print "attempting selling at delta: %s for price %s" % (
                    DeltaList, price
                )
                _attemptSell(price)
                buy_flag = False
        except:
            try:
                price = price*adjust
                print "attempting selling at delta: %s for price %s" % (
                    delta, price
                )
                _attemptSell(price)
                buy_flag = False
            except:
                try:
                    price = price*adjust
                    print "attempting selling at delta: %s for price %s" % (
                        delta, price
                    )
                    _attemptSell(price)
                    buy_flag = False
                except:
                    print "sell failed"
                    pass
    counter += 1
    if killer.kill_now:
        break
print "End of the program. I was killed gracefully :)"
