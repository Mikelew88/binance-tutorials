import websocket, json, pprint, talib, numpy
import config
from binance.client import Client
from binance.enums import *

SOCKET = "wss://stream.binance.com:9443/ws/ethusdt@kline_1m"

RSI_PERIOD = 8
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = "ETHUSD"
TRADE_QUANTITY = 0.02
ORDER_TYPE_MARKET = "MARKET"
SIDE_BUY = "BUY"
SIDE_SELL = "SELL"
MAX_POSTITIONS = 5
POSITION_DECAY = 0

closes = []
n_positions = 0

client = Client(config.API_KEY, config.API_SECRET, tld="us")


def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(
            symbol=symbol, side=side, type=order_type, quantity=quantity
        )
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True


def on_open(ws):
    print("opened connection")


def on_close(ws):
    print("closed connection")


def on_message(ws, message):
    global closes, n_positions

    print("received message")
    json_message = json.loads(message)
    pprint.pprint(json_message)

    candle = json_message["k"]

    is_candle_closed = candle["x"]
    close = candle["c"]

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))

        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            last_rsi = rsi[-1]

            if last_rsi > RSI_OVERBOUGHT - (n_positions * POSITION_DECAY):
                if n_positions > 1:
                    print("Overbought! Sell! Sell! Sell!")
                    # put binance sell logic here
                    order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        n_positions -= 1
                else:
                    print("It is overbought, but we don't own any. Nothing to do.")

            if last_rsi < RSI_OVERSOLD - (n_positions * POSITION_DECAY):
                if n_positions <= MAX_POSTITIONS:
                    print("It is oversold, but you already own max postitions, nothing to do.")
                else:
                    print("Oversold! Buy! Buy! Buy!")
                    # put binance buy order logic here
                    order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                    if order_succeeded:
                        n_positions += 1


ws = websocket.WebSocketApp(
    SOCKET, on_open=on_open, on_close=on_close, on_message=on_message
)
ws.run_forever()