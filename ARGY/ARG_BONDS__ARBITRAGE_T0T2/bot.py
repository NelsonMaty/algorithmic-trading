import requests
# import json

import pandas as pd
from datetime import datetime

# //////////////////////////////////////#
#              CONSTANTS               #
# //////////////////////////////////////#

HOUR_MARKET_OPEN = 11
HOUR_MARKET_CLOSE = 16

URL__API_IOL__BASE = "https://api.invertironline.com/"
URL__API_IOL__TOKEN = URL__API_IOL__BASE + "token"

URL__API_IOL__V2 = URL__API_IOL__BASE + "api/v2/"
URL__API_IOL__BONDS = URL__API_IOL__V2 + "Cotizaciones/bonos/bonos/argentina"
URL__API_IOL__ACCOUNT = URL__API_IOL__V2 + "estadocuenta"
URL__API_IOL__ASSET_DATA = URL__API_IOL__V2 + "{Mercado}/Titulos/{Simbolo}/Cotizacion"

# TODO: read from env
SECRET__USER_IOL = ""
SECRET__PASS_IOL = ""

TIMEFRAME = "t0"

request_headers = {}


def isMarketOpen():
    current_hour = datetime.now().hour
    return (current_hour >= HOUR_MARKET_OPEN) and (current_hour < HOUR_MARKET_CLOSE)


def get_request_headers():
    request_token_data = {
        "username": SECRET__USER_IOL,
        "password": SECRET__PASS_IOL,
        "grant_type": "password",
    }

    request_token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    r = requests.post(
        url=URL__API_IOL__TOKEN, data=request_token_data, headers=request_token_headers
    )

    return {"Authorization": "Bearer " + r.json()["access_token"]}


def get_all_argy_dollar_bonds(request_headers):
    return [
        "AE38D",
        "AL29D",
        "AL30D",
        "AL35D",
        "AL41D",
        "AY24D",
        "GD29D",
        "GD30D",
        "GD35D",
        "GD38D",
        "GD41D",
        "GD46D",
    ]
    # request_bonds_data = {
    #     'panelCotizacion': {
    #         'pais': 'argentina',
    #         'instrumento': 'bonos'
    #     }
    # }

    # r = requests.get(url=URL__API_IOL__BONDS,
    #                  data=request_bonds_data, headers=request_headers)

    # df = pd.DataFrame.from_dict(r.json()['titulos'])
    # dollar_bonds = df[(df['moneda'] == 'US$')][df['simbolo'].str.endswith('D')]
    # return dollar_bonds['simbolo'].values


def main(request_headers):
    # watchlist = ['AL30C', 'AL30D', 'AL30', 'GD30C', 'GD30D', 'GD30']
    watchlist = ["AL30C", "AL30D"]

    request_asset_data = {
        "mercado": "argentina",
        "model.mercado": "bCBA",
    }

    prices = pd.DataFrame(columns=["Date", "Symbol", "Bid_T2", "Offer_T0", "PnL"])

    for bond in watchlist:
        request_asset_data["simbolo"] = bond
        request_asset_data["model.simbolo"] = bond
        request_asset_data["model.plazo"] = "t0"

        puntas_CI = pd.DataFrame(
            requests.get(
                url=URL__API_IOL__ASSET_DATA,
                params=request_asset_data,
                headers=request_headers,
            ).json()["puntas"]
        )

        request_asset_data["model.plazo"] = "t2"

        puntas_T2 = pd.DataFrame(
            requests.get(
                url=URL__API_IOL__ASSET_DATA,
                params=request_asset_data,
                headers=request_headers,
            ).json()["puntas"]
        )

        gap = (
            (puntas_T2.iloc[0]["precioCompra"] - puntas_CI.iloc[0]["precioVenta"])
            * 100
            / puntas_CI.iloc[0]["precioVenta"]
        )

        prices = prices.append(
            {
                "Date": datetime.now(),
                "Symbol": bond,
                "Bid_T2": puntas_T2.iloc[0]["precioCompra"],
                "Offer_T0": puntas_CI.iloc[0]["precioVenta"],
                "PnL": gap,
            },
            ignore_index=True,
        )

        print(
            "Compra:",
            puntas_CI.iloc[0]["precioVenta"],
            "- Venta:",
            puntas_T2.iloc[0]["precioCompra"],
            "- PNL:",
            gap,
        )

    file_name = datetime.today().strftime("%Y-%m-%d") + ".xlsx"

    try:
        previous_dataframe = pd.read_excel(file_name)
    except FileNotFoundError:
        previous_dataframe = pd.DataFrame()

    prices = previous_dataframe.append(prices)

    prices.to_excel(file_name, index=False)


if isMarketOpen():
    request_headers = get_request_headers()
    main(request_headers)
