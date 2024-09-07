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
API_SECRET = ""

CURRENCY = "ETHUSDT"

AROON_LENGTH = 30
SMA_REGRESSION_LENGTH = 15
VOLUME_LENGTH = 10
VOLUME_THRESHOLD = 1.5
NATR_THRESHOLD = 0.37
NATR_LENGTH = 2
BULL_BEAR_MARKET_EMA_THRESHOLD = 300
LEVERAGE = 5


# //////////////////////////////////////#
#            CONFIGURATIONS            #
# //////////////////////////////////////#
logging.basicConfig(filename="bot.log", level=logging.INFO)
logger = logging.getLogger("ETHUSDT_1M_MEAN_REVERSION")

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
        # delete unwanted data - just keep date, open, high, low, close, volume
        del line[6:]
        # cast string numbers to integer
        formated_bars.append(list(map(cast_string_to_float, line)))

    dataframe = pd.DataFrame(
        formated_bars, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
    )
    dataframe.set_index("Date", inplace=True)
    dataframe.index = pd.to_datetime(dataframe.index)

    return dataframe


# //////////////////////////////////////#
#         TECHNICAL INDICATORS         #
# //////////////////////////////////////#


def add_AROON(dataframe, column_name_up, column_name_down, length):
    aroon_down, aroon_up = talib.AROON(
        dataframe["High"], dataframe["Low"], timeperiod=length
    )
    dataframe[column_name_down] = aroon_down
    dataframe[column_name_up] = aroon_up


def add_NATR(dataframe, column_name, length):
    dataframe[column_name] = talib.NATR(
        dataframe["High"], dataframe["Low"], dataframe["Close"], timeperiod=length
    )


def add_VOLUME_AVG(dataframe, column_name, length):
    dataframe[column_name] = dataframe["Volume"].rolling(length).mean()


def add_SMA(dataframe, column_name, length):
    dataframe[column_name] = dataframe["Close"].rolling(length).mean()


def add_EMA(dataframe, column_name, length):
    dataframe[column_name] = dataframe["Close"].ewm(span=length).mean()

    # //////////////////////////////////////#
    #           MARKET STRATEGY            #
    # //////////////////////////////////////#


def get_next_market_action(dataframe, current_position):
    current_market_data = dataframe.iloc[-1, :]
    next_market_action = MarketActions.IDLE

    if current_position != 0:
        if (
            current_position > 0
            and current_market_data["Close"] > current_market_data["mean_to_regress"]
        ):
            next_market_action = MarketActions.CLOSE
        elif (
            current_position < 0
            and current_market_data["Close"] < current_market_data["mean_to_regress"]
        ):
            next_market_action = MarketActions.CLOSE
    else:
        if current_market_data["natr"] > NATR_THRESHOLD:
            if (
                current_market_data["aroon_up"] == 100
                and current_market_data["Volume"]
                > (2 * current_market_data["volume_avg"])
                and current_market_data["Close"] < current_market_data["bear_bull_ema"]
            ):
                next_market_action = MarketActions.SELL
        elif (
            current_market_data["aroon_down"] == 100
            and current_market_data["Volume"] > (2 * current_market_data["volume_avg"])
            and current_market_data["Close"] > current_market_data["bear_bull_ema"]
        ):
            next_market_action = MarketActions.BUY
    return next_market_action


# //////////////////////////////////////#
#              MAIN LOGIC              #
# //////////////////////////////////////#


def calculateQuantity(price, walletBalance):
    quantity = str(walletBalance / (price))
    rounded_quantity = float(
        quantity[: quantity.find(".") + 4]  # taking 3 decimals
    )

    return round(rounded_quantity * LEVERAGE, 6)


@log_if_error
def main():
    # Get data from binance
    client = Client(API_KEY, API_SECRET, {"timeout": 30})
    futures_account = client.futures_account()
    current_position = float(
        next(
            item
            for item in futures_account.get("positions")
            if item["symbol"] == CURRENCY
        ).get("positionAmt")
    )
    klines = client.get_klines(
        symbol=CURRENCY,
        interval=Client.KLINE_INTERVAL_1MINUTE,
        limit=BULL_BEAR_MARKET_EMA_THRESHOLD,
    )
    dataframe = format_klines_into_OHLC(klines)

    # Add technical indicators
    add_AROON(dataframe, "aroon_up", "aroon_down", AROON_LENGTH)
    add_NATR(dataframe, "natr", NATR_LENGTH)
    add_VOLUME_AVG(dataframe, "volume_avg", VOLUME_LENGTH)
    add_SMA(dataframe, "mean_to_regress", SMA_REGRESSION_LENGTH)
    add_EMA(dataframe, "bear_bull_ema", BULL_BEAR_MARKET_EMA_THRESHOLD)

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
