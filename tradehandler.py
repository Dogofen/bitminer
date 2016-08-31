# Copyright (c) 2013 Alan McIntyre

import threading
import time
import btceapi
import ema


def _runHandler(trade_handler):
    last_tid = False
    while trade_handler.running:
        conn = btceapi.BTCEConnection()
        loop_start = time.time()
        interval = trade_handler.collectionInterval

        p = trade_handler.type
        try:
            trade_handler.asks, trade_handler.bids = btceapi.getDepth(p, conn)
        except:
            print "getDepth Error"
        # Collect the set of handlers for which we should get trade history.
        try:
            tradeHistory = btceapi.getTradeHistory(p, conn)
            if tradeHistory[0].tid != last_tid:
                trade_handler.tradeHistory = tradeHistory
                last_tid = trade_handler.arrangePriceHistory(tradeHistory)
        except:
            print "getTradeHistory Error"
        conn.close()

        while trade_handler.running and time.time() - loop_start < interval:
            time.sleep(0.5)

    # Give traders and opportunity to do thread-specific cleanup.


class TradeHandler(object):
    def __init__(self, pair, key, collectionInterval=1, bufferSpanMinutes=10):
        self.bufferSpanMinutes = bufferSpanMinutes
        handler = btceapi.KeyHandler(key)
        key = handler.getKeys()[0]
        print "Trading with key %s" % key
        self.api = btceapi.TradeAPI(key, handler)
        self.type = pair
        self.fee_adjustment = 1 - float(btceapi.getTradeFee(self.type))/10
        self.collectionInterval = collectionInterval
        self.running = False
        self.bidHistory = {}
        self.askHistory = {}
        self.asks = []
        self.bids = []

    def setCollectionInterval(self, interval_seconds):
        self.collectionInterval = interval_seconds

    def arrangePriceHistory(self, trade_history):
        self.askHistory['time'] = []
        self.bidHistory['time'] = []
        self.askHistory['price'] = []
        self.bidHistory['price'] = []
        for t in trade_history:
            if t.trade_type == 'bid':
                self.bidHistory['time'].extend([t.date])
                self.bidHistory['price'].extend([t.price])
            else:
                self.askHistory['time'].extend([t.date])
                self.askHistory['price'].extend([t.price])

        return trade_history[0].tid

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=_runHandler, args=(self,))
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

    def _attemptBuy(self, price, amount):
        conn = btceapi.BTCEConnection()
        info = self.api.getInfo(conn)
        curr1, curr2 = self.type.split("_")
        # Limit order to what we can afford to buy.
        available = float(getattr(info, "balance_" + curr2))
        max_buy = available / price
        buy_amount = min(max_buy, amount) * self.fee_adjustment
        print "attempting to buy %s %s at %s for %s %s" % (
            buy_amount, curr1.upper(), price, buy_amount*price,
            curr2.upper())
        r = self.api.trade(self.type, "buy", price, str(buy_amount), conn)
        print "\tReceived %s %s" % (r.received, curr1.upper())
        # If the order didn't fill completely, cancel the remaining order
        if r.order_id != 0:
            print "\tCanceling unfilled portion of order"
            self.api.cancelOrder(r.order_id, conn)
        conn.close()
