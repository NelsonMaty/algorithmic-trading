from binance import Client
from datetime import datetime
from enum import Enum

import logging
import pandas as pd
import talib
import numpy as np

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
SMA_LENGTH = 3
THRESHOLD = 0
CURRENCY = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_1MINUTE
LEVERAGE = 3


# //////////////////////////////////////#
#            CONFIGURATIONS            #
# //////////////////////////////////////#
logging.basicConfig(filename="bot.log", level=logging.INFO)
# logging.basicConfig(level=logging.INFO)

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("BTCUSDT_1M_TREND_FOLLOW")

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


def add_SMA(dataframe, column_name, length):
    dataframe[column_name] = talib.SMA(dataframe["Close"], timeperiod=length)
    dataframe.dropna(inplace=True)


def add_GRADIENT(dataframe, column_name):
    dataframe[column_name] = np.gradient(dataframe["sma"])


# //////////////////////////////////////#
#          STRATEGY FUNCTIONS          #
# //////////////////////////////////////#


def calculateQuantity(price, walletBalance):
    quantity = str(walletBalance / (price) * LEVERAGE)
    rounded_quantity = float(
        quantity[: quantity.find(".") + 4]  # taking 3 decimals
    )

    return rounded_quantity


# //////////////////////////////////////#
#           MARKET STRATEGY            #
# //////////////////////////////////////#


def get_next_market_action(dataframe, current_position):
    current_market_data = dataframe.iloc[-1, :]
    next_market_action = MarketActions.IDLE

    if current_position != 0:
        if current_position > 0 and current_market_data["gradient"] < THRESHOLD:
            next_market_action = MarketActions.SELL
        elif current_position < 0 and current_market_data["gradient"] >= THRESHOLD:
            next_market_action = MarketActions.BUY
    else:
        if current_market_data["gradient"] >= THRESHOLD:
            next_market_action = MarketActions.BUY
        else:
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
        symbol=CURRENCY, interval=INTERVAL, limit=SMA_LENGTH + 10
    )
    dataframe = format_klines_into_OHLC(klines)

    # Add technical indicators
    add_SMA(dataframe, "sma", SMA_LENGTH)
    add_GRADIENT(dataframe, "gradient")

    # Run strategy
    action_to_perform = get_next_market_action(dataframe, current_position)

    # Execute action
    if action_to_perform is MarketActions.BUY:  # open long position
        ask_price = float(client.futures_order_book(symbol=CURRENCY).get("asks")[0][0])
        quantity = calculateQuantity(
            ask_price, float(futures_account.get("totalWalletBalance"))
        )
        client.futures_create_order(
            symbol=CURRENCY,
            side="BUY",
            type="MARKET",
            quantity=quantity * 2,  # TODO: use multiplier only when fliping a position
        )
    elif action_to_perform is MarketActions.SELL:  # open short position
        bid_price = float(client.futures_order_book(symbol=CURRENCY).get("bids")[0][0])
        quantity = calculateQuantity(
            bid_price, float(futures_account.get("totalWalletBalance"))
        )
        client.futures_create_order(
            symbol=CURRENCY,
            side="SELL",
            type="MARKET",
            quantity=quantity * 2,  # TODO: use multiplier only when fliping a position
        )

    logger.info(
        "[%s] - %s", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), action_to_perform
    )


main()
