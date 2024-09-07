from binance import Client
from datetime import datetime
from enum import Enum

import logging
import pandas as pd
import talib

# //////////////////////////////////////#
#          ACTIONS DEFINITIONS         #
# //////////////////////////////////////#


class MarketActions(Enum):
    BUY = "BUY"
    SELL = "SELL"
    IDLE = "NO ACTION NEEDED"
    CLOSE = "CLOSE POSTION"

    def __str__(self):
        return self.value


# //////////////////////////////////////#
#              CONSTANTS               #
# //////////////////////////////////////#


# TODO: use env variables
API_KEY = ""
# TODO: use env variables
API_SECRET = ""
CURRENCY = "BTCUSDT"

AROON_LENGTH = 180

UPPER_THRESHOLD = 91
TAKE_PROFIT_UP_THRESHOLD = 12

LOWER_THRESHOLD = -16
TAKE_PROFIT_DOWN_THRESHOLD = -12


# //////////////////////////////////////#
#            CONFIGURATIONS            #
# //////////////////////////////////////#
logging.basicConfig(filename="bot.log", level=logging.INFO)
logger = logging.getLogger("BTCUSDT_5M_TREND_FOLLOW")

# //////////////////////////////////////#
#           LOGGER DECORATOR           #
# //////////////////////////////////////#


def log_if_error(function):
    def exception_handler(*args, **kwargs):
        try:
            result = function(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(
                "[%s]", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), exc_info=e
            )

    return exception_handler


# //////////////////////////////////////#
#            DATA FORMATTER            #
# //////////////////////////////////////#


@log_if_error
def format_klines_into_OHLC(klines):
    def cast_string_to_float(data):
        if type(data) == str:
            casted_data = float(data)
        else:
            casted_data = datetime.fromtimestamp(data / 1000.0)
        return casted_data

    formated_bars = []

    for line in klines:
        # delete unwanted data - just keep date, open, high, low, close
        del line[5:]
        # cast string numbers to integer
        formated_bars.append(list(map(cast_string_to_float, line)))

    dataframe = pd.DataFrame(
        formated_bars, columns=["Date", "Open", "High", "Low", "Close"]
    )
    dataframe.set_index("Date", inplace=True)
    dataframe.index = pd.to_datetime(dataframe.index)

    return dataframe


# //////////////////////////////////////#
#         TECHNICAL INDICATORS         #
# //////////////////////////////////////#


def add_AROONOSC(dataframe, colum_name, lenght):
    dataframe[colum_name] = talib.AROONOSC(
        dataframe["High"], dataframe["Low"], timeperiod=lenght
    )


# //////////////////////////////////////#
#          STRATEGY FUNCTIONS          #
# //////////////////////////////////////#


def is_market_uptrending(data):
    return data["Aroon_Oscilator"] >= TAKE_PROFIT_UP_THRESHOLD


def is_market_downtrending(data):
    return data["Aroon_Oscilator"] <= TAKE_PROFIT_DOWN_THRESHOLD


def is_market_volatility_low(data):
    return True


def hasPriceUpMomentum(dataframe):
    current_value = dataframe.iloc[-1, :]

    return current_value["Aroon_Oscilator"] >= UPPER_THRESHOLD


def hasPriceDownMomentum(dataframe):
    current_value = dataframe.iloc[-1, :]

    return current_value["Aroon_Oscilator"] <= LOWER_THRESHOLD


def calculateQuantity(price, walletBalance):
    quantity = str(walletBalance / (price))
    rounded_quantity = float(
        quantity[: quantity.find(".") + 4]  # taking 3 decimals
    )

    return round(rounded_quantity * 3, 6)  # LEVERAGE


# //////////////////////////////////////#
#           MARKET STRATEGY            #
# //////////////////////////////////////#


def get_next_market_action(dataframe, current_position):
    current_market_data = dataframe.iloc[-1, :]
    next_market_action = MarketActions.IDLE

    if current_position != 0:
        if current_position > 0 and not is_market_uptrending(current_market_data):
            next_market_action = MarketActions.CLOSE
        elif current_position < 0 and not is_market_downtrending(current_market_data):
            next_market_action = MarketActions.CLOSE
    else:
        if hasPriceUpMomentum(dataframe):
            next_market_action = MarketActions.BUY
        elif hasPriceDownMomentum(dataframe):
            next_market_action = MarketActions.SELL
    return next_market_action


# //////////////////////////////////////#
#              MAIN LOGIC              #
# //////////////////////////////////////#


@log_if_error
def main():
    # Get data from binance
    client = Client(API_KEY, API_SECRET, {"timeout": 30})
    futures_account = client.futures_account()
    current_position = float(
        next(
            item
            for item in futures_account.get("positions")
            if item["symbol"] == "BTCUSDT"
        ).get("positionAmt")
    )
    klines = client.get_klines(
        symbol=CURRENCY, interval=Client.KLINE_INTERVAL_5MINUTE, limit=500
    )
    dataframe = format_klines_into_OHLC(klines)

    # Add technical indicators
    add_AROONOSC(dataframe, "Aroon_Oscilator", AROON_LENGTH)

    # Run strategy
    action_to_perform = get_next_market_action(dataframe, current_position)

    # Execute action
    if action_to_perform is MarketActions.BUY:  # open long position
        ask_price = float(client.futures_order_book(symbol=CURRENCY).get("asks")[0][0])
        quantity = calculateQuantity(
            ask_price, float(futures_account.get("totalWalletBalance"))
        )
        client.futures_create_order(
            symbol=CURRENCY, side="BUY", type="MARKET", quantity=quantity
        )
    elif action_to_perform is MarketActions.SELL:  # open short position
        bid_price = float(client.futures_order_book(symbol=CURRENCY).get("bids")[0][0])
        quantity = calculateQuantity(
            bid_price, float(futures_account.get("totalWalletBalance"))
        )
        client.futures_create_order(
            symbol=CURRENCY, side="SELL", type="MARKET", quantity=quantity
        )
    elif action_to_perform is MarketActions.CLOSE:  # close open position
        market_side = "SELL" if (current_position > 0) else "BUY"
        client.futures_create_order(
            symbol=CURRENCY,
            side=market_side,
            type="MARKET",
            quantity=abs(current_position),
        )

    logger.info(
        "[%s] - %s",
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        action_to_perform,
    )


main()
