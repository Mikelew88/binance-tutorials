import backtrader as bt
import datetime

start_time = "2021-01-19"
end_time = "2021-04-23"

MAX_POSITIONS = 1000
POSITION_DECAY = 0
BUY_SELL_DESIRE_DECAY = 0
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
PERIOD = 8


class RSIStrategy(bt.Strategy):
    def __init__(
        self, rsi_overbought=RSI_OVERBOUGHT, rsi_oversold=RSI_OVERSOLD, period=PERIOD
    ):
        # 4*10
        self.rsi = bt.talib.RSI(self.data, timeperiod=period)
        self.periods_without_buy = 0
        self.periods_without_sell = 0
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.period = period

    def next(self):
        self.periods_without_buy += 1
        self.periods_without_sell += 1
        last_rsi = self.rsi[-1]
        if (
            last_rsi
            < (
                self.rsi_oversold
                + (self.periods_without_buy * BUY_SELL_DESIRE_DECAY)
                - (self.position.size * POSITION_DECAY)
            )
            and self.position.size <= MAX_POSITIONS
        ):
            self.buy(size=1)
            self.periods_without_buy = 0

        if (
            last_rsi
            > (
                self.rsi_overbought
                - (self.periods_without_sell * BUY_SELL_DESIRE_DECAY)
                - (self.position.size * POSITION_DECAY)
            )
            and self.position.size > 0
        ):
            self.close()
            self.periods_without_sell = 0

    def stop(self):
        print(
            "(Period %2d) (RSI_OVER_BOUGHT %2d) (RSI_OVER_SOLD %2d) Ending Value %.2f"
            % (
                self.period,
                self.rsi_overbought,
                self.rsi_oversold,
                self.broker.getvalue(),
            )
        )


import config, csv
from binance.client import Client

client = Client(config.API_KEY, config.API_SECRET)

csvfile = open("coinview/data/backtest.csv", "w", newline="")
candlestick_writer = csv.writer(csvfile, delimiter=",")

candlesticks = client.get_historical_klines(
    "ETHUSDT", Client.KLINE_INTERVAL_15MINUTE, start_time, end_time
)

for candlestick in candlesticks:
    candlestick[0] = candlestick[0] / 1000
    candlestick_writer.writerow(candlestick)

csvfile.close()

cerebro = bt.Cerebro()

fromdate = datetime.datetime.strptime(start_time, "%Y-%m-%d")
todate = datetime.datetime.strptime(end_time, "%Y-%m-%d")

data = bt.feeds.GenericCSVData(
    dataname="coinview/data/backtest.csv",
    dtformat=2,
    compression=15,
    timeframe=bt.TimeFrame.Minutes,
    fromdate=fromdate,
    todate=todate,
)

# cerebro.optstrategy(
#     RSIStrategy,
#     # rsi_overbought=range(70, 100, 5),
#     # rsi_oversold=range(10, 35, 5),
#     period=range(4, 4*60, 4)
# )

cerebro.addstrategy(RSIStrategy)

cerebro.adddata(data)

cerebro.run(maxcpus=1)

cerebro.plot()