import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from time import sleep
from mt5_config import login_number, path


def get_indicators():
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, period)

    open_prices = []
    for rate in rates:
        open_price = rate[1]
        open_prices.append(open_price)

    open_series = pd.Series(open_prices)

    sma = open_series.mean()
    std = open_series.std()

    return sma, std

def get_exposure(symbol):
    positions = mt5.positions_get(symbol=symbol)

    exposure = 0
    for pos in positions:
        if pos.type == 0:  # buy
            exposure += pos.volume
        elif pos.type == 1:  # sell
            exposure -= pos.volume

    return exposure


def send_market_order(symbol, order_type, volume, sl=0.0, tp=0.0):
    # market order

    action = mt5.TRADE_ACTION_DEAL

    def get_market_price(symbol, type):
        if type == mt5.ORDER_TYPE_BUY:
            return mt5.symbol_info(symbol).ask
        elif type == mt5.ORDER_TYPE_SELL:
            return mt5.symbol_info(symbol).bid

    request = {
        "action": action,
        "symbol": symbol,
        "volume": volume,  # float
        "type": order_type,
        "price": get_market_price(symbol, order_type),
        "sl": sl,  # float
        "tp": tp,  # float
        "deviation": 20,
        "magic": 1,
        "comment": "python market order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # some brokers accept mt5.ORDER_FILLING_FOK only
    }

    res = mt5.order_send(request)
    return res


def close_position(symbol, where_type=None):
    # close position

    # where type either buy or sell
    positions = mt5.positions_get(symbol=symbol)
    print('open positions', positions)

    for pos in positions:
        if pos.type == where_type:
            pos_to_close = pos
            break

    def reverse_type(type):
        # to close a buy positions, you must perform a sell position and vice versa
        if type == mt5.ORDER_TYPE_BUY:
            return mt5.ORDER_TYPE_SELL
        elif type == mt5.ORDER_TYPE_SELL:
            return mt5.ORDER_TYPE_BUY

    def get_close_price(symbol, type):
        if type == mt5.ORDER_TYPE_BUY:
            return mt5.symbol_info(symbol).bid
        elif type == mt5.ORDER_TYPE_SELL:
            return mt5.symbol_info(symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": pos_to_close.ticket,
        "symbol": pos_to_close.symbol,
        "volume": pos_to_close.volume,
        "type": reverse_type(pos_to_close.type),
        "price": get_close_price(pos_to_close.symbol, pos_to_close.type),
        "deviation": 20,
        "magic": 0,
        "comment": "python close order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,  # some brokers accept mt5.ORDER_FILLING_FOK only
    }

    res = mt5.order_send(request)
    return res

if __name__ == '__main__':
    # start the platform with initialize()
    result = mt5.initialize(path)
    if login_number == mt5.account_info().login and result is True:
        print('Connection with MT5 established')
    else:
        print('Connection failed')
        mt5.shutdown()

    # General Strategy Parameters - Symbol, Timeframe, Bollinger Period, How many Standard deviations
    symbol = 'EURCHF'
    timeframe = mt5.TIMEFRAME_M1

    volume = 1.0

    period = 20
    num_std = 1.5

    while True:
        print(datetime.now())
        # Account Data - Balance, Equity
        account_data = mt5.account_info()
        balance = account_data.balance
        equity = account_data.equity

        print('Balance:', balance)
        print('Equity:', equity)

        # Market Data - Bid Ask Prices
        prices = mt5.symbol_info_tick(symbol)
        bid = prices.bid
        ask = prices.ask
        print('Prices Bid/Ask:', bid, ask)

        # Historical Data - Bollinger Band Indicators
        sma, std = get_indicators()
        lower_band = sma - std * num_std
        upper_band = sma + std * num_std

        print('SMA:', sma)
        print('STD:', std)
        print('Lower/Upper Bands', lower_band, upper_band)

        # Exposure on our Symbol
        exposure = get_exposure(symbol)
        print('Exposure:', exposure)

        entry_signal = None
        exit_signal = None

        # Signal Function
        if ask < lower_band:
            entry_signal = 'buy'
        elif bid > upper_band:
            entry_signal = 'sell'

        # Exit Signal Function
        if bid > sma:
            exit_signal = 'sell'  # close buy position
        elif ask < sma:
            exit_signal = 'buy'  # close sell position

        print('Entry signal:', entry_signal)
        print('Exit signal:', exit_signal)

        # Submit Trades
        if entry_signal == 'buy' and exposure == 0:
            print('Entering Buy')

            order_result = send_market_order(symbol, mt5.ORDER_TYPE_BUY, volume)
            print(order_result)

        elif entry_signal == 'sell' and exposure == 0:
            print('Entering Sell')

            order_result = send_market_order(symbol, mt5.ORDER_TYPE_SELL, volume)
            print(order_result)

        if exit_signal == 'buy' and exposure <= -1:
            print('Closing Sell Positions')

            close_order_result = close_position(symbol, where_type=mt5.ORDER_TYPE_SELL)
            print(close_order_result)

        elif exit_signal == 'sell' and exposure >= 1:
            print('Closing Buy Positions')

            close_order_result = close_position(symbol, where_type=mt5.ORDER_TYPE_BUY)
            print(close_order_result)

        print('--\n')
        sleep(1)