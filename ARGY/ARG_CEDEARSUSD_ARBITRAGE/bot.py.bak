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
URL__API_IOL__CEDEARS = URL__API_IOL__V2 + "Cotizaciones/acciones/cedears/argentina"
URL__API_IOL__ACCOUNT = URL__API_IOL__V2 + "estadocuenta"
URL__API_IOL__ASSET_DATA = URL__API_IOL__V2 + "{Mercado}/Titulos/{Simbolo}/Cotizacion"
# TODO: read from env
SECRET__USER_IOL = ""
SECRET__PASS_IOL = ""

TIMEFRAME = "t0"
COMISSION = 0.375  # comission + market + IVA
RISK_THRESHOLD = 2  # TBD

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


def get_all_argy_dollar_cedears(request_headers):
    request_cedears_data = {
        "panelCotizacion": {
            "pais": "argentina",
            "instrumento": "acciones",
            "panel": "cedears",
        }
    }

    r = requests.get(
        url=URL__API_IOL__CEDEARS, data=request_cedears_data, headers=request_headers
    )

    df = pd.DataFrame.from_dict(r.json()["titulos"])
    cedears = df[(df["moneda"] == "US$")][df["simbolo"].str.endswith("D")]
    return cedears["simbolo"].values


def main(request_headers):
    cedears_list = get_all_argy_dollar_cedears(request_headers)

    request_asset_data = {
        "mercado": "argentina",
        "model.mercado": "bCBA",
        "model.plazo": "t0",
    }
    mep_dataframe = pd.DataFrame(columns=["Date", "Symbol", "Sell_price"])

    for cedear in cedears_list:
        cedear_name = cedear[:-1]
        request_asset_data["simbolo"] = cedear_name
        request_asset_data["model.simbolo"] = cedear_name
        peso_cedear = requests.get(
            url=URL__API_IOL__ASSET_DATA,
            params=request_asset_data,
            headers=request_headers,
        )
        if peso_cedear.status_code == 200:
            punta_pesos = pd.DataFrame(peso_cedear.json()["puntas"])
            if len(punta_pesos) != 0:
                request_asset_data["simbolo"] = cedear
                request_asset_data["model.simbolo"] = cedear
                dollar_cedear = requests.get(
                    url=URL__API_IOL__ASSET_DATA,
                    params=request_asset_data,
                    headers=request_headers,
                )
                if dollar_cedear.status_code == 200:
                    punta_dollar = pd.DataFrame(dollar_cedear.json()["puntas"])
                    if len(punta_dollar) != 0:
                        venta_mep = (
                            punta_pesos.iloc[0]["precioCompra"]
                            / punta_dollar.iloc[0]["precioVenta"]
                        )
                        mep_dataframe = mep_dataframe.append(
                            {
                                "Date": datetime.now(),
                                "Symbol": cedear_name,
                                # 'Buy_price': compra_mep,
                                "Sell_price": venta_mep,
                            },
                            ignore_index=True,
                        )

    request_asset_data = {
        "mercado": "argentina",
        "simbolo": "AL30",
        "model.simbolo": "AL30",
        "model.mercado": "bCBA",
        "model.plazo": "t0",
    }

    puntas_al30 = pd.DataFrame(
        requests.get(
            url=URL__API_IOL__ASSET_DATA,
            params=request_asset_data,
            headers=request_headers,
        ).json()["puntas"]
    )

    request_asset_data["model.simbolo"] = "AL30D"
    request_asset_data["simbolo"] = "AL30D"

    puntas_al30D = pd.DataFrame(
        requests.get(
            url=URL__API_IOL__ASSET_DATA,
            params=request_asset_data,
            headers=request_headers,
        ).json()["puntas"]
    )

    compra_mep_al30 = (
        puntas_al30.iloc[0]["precioVenta"] / puntas_al30D.iloc[0]["precioCompra"]
    )
    request_asset_data = {
        "mercado": "argentina",
        "simbolo": "GD30",
        "model.simbolo": "GD30",
        "model.mercado": "bCBA",
        "model.plazo": "t0",
    }

    puntas_gd30 = pd.DataFrame(
        requests.get(
            url=URL__API_IOL__ASSET_DATA,
            params=request_asset_data,
            headers=request_headers,
        ).json()["puntas"]
    )

    request_asset_data["model.simbolo"] = "GD30D"
    request_asset_data["simbolo"] = "GD30D"

    puntas_gd30D = pd.DataFrame(
        requests.get(
            url=URL__API_IOL__ASSET_DATA,
            params=request_asset_data,
            headers=request_headers,
        ).json()["puntas"]
    )

    compra_mep_gd30 = (
        puntas_gd30.iloc[0]["precioVenta"] / puntas_gd30D.iloc[0]["precioCompra"]
    )

    mep_dataframe["Sell_spread_al30"] = (
        mep_dataframe["Sell_price"] / compra_mep_al30
    ) - 1
    mep_dataframe["Sell_spread_gd30"] = (
        mep_dataframe["Sell_price"] / compra_mep_gd30
    ) - 1

    file_name = datetime.today().strftime("%Y-%m-%d") + "-cedears.xlsx"

    try:
        previous_dataframe = pd.read_excel(file_name)
    except FileNotFoundError:
        previous_dataframe = pd.DataFrame()

    # mep_dataframe.reset_index(inplace=True)

    mep_dataframe = previous_dataframe.append(mep_dataframe)

    # mep_dataframe['uuid'] = [uuid.uuid4()
    #                          for _ in range(len(mep_dataframe.index))]
    mep_dataframe.to_excel(file_name, index=False)
    # current_buy_mep_al30 = get_buy_mep_al30()  # TODO: get cheapest mep

    # for bond in dollar_bonds_list:
    #     ask = get_ask_dollar_bond(bond)
    #     bid = get_bid_peso_bond(bond)
    #     if (should_sell_mep(ask, bid)):
    #         sell_dollar_mep(bond, ask, bid)
    #         buy_al30(current_buy_mep_al30)
    #         update_current_buy_mep_al30(current_buy_mep_al30)

    # TODO: check CEDEARs


if isMarketOpen():
    request_headers = get_request_headers()
    main(request_headers)
