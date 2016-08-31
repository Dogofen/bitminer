# Copyright (c) 2013 Alan McIntyre

class TraderBase(object):
    def __init__(self, pairs):
        self.pairs = pairs
    
    def onNewDepth(self, t, pair, asks, bids):
        print "new depth in pair:%s ask:%s bid:%s" % (pair, asks[0], bids[0])
        pass

    def onNewTradeHistory(self, t, pair, trades):
        print "new trade %s" % trades[0].price
        pass
        
    def onLoopEnd(self, t):
        pass
    
    def onExit(self):
        pass
    
