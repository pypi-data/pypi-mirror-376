#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2022 fx-kirin <fx.kirin@gmail.com>
#
# Distributed under terms of the MIT license.

"""

"""
import pandas as pd
from kanirequests import KaniRequests


def get_nehaba_limit(last_execution):
    if last_execution < 200:
        return 5
    if last_execution < 500:
        return 8
    if last_execution < 700:
        return 10
    if last_execution < 1000:
        return 15
    if last_execution < 1500:
        return 30
    if last_execution < 2000:
        return 40
    if last_execution < 3000:
        return 50
    if last_execution < 5000:
        return 70
    if last_execution < 7000:
        return 100
    if last_execution < 10000:
        return 150
    if last_execution < 15000:
        return 300
    if last_execution < 20000:
        return 400
    if last_execution < 30000:
        return 500
    if last_execution < 50000:
        return 700
    if last_execution < 70000:
        return 1000
    if last_execution < 100000:
        return 1500
    if last_execution < 150000:
        return 3000
    if last_execution < 200000:
        return 4000
    if last_execution < 300000:
        return 5000
    if last_execution < 500000:
        return 7000
    if last_execution < 700000:
        return 10000
    if last_execution < 1000000:
        return 15000
    if last_execution < 1500000:
        return 30000
    if last_execution < 2000000:
        return 40000
    if last_execution < 3000000:
        return 50000
    if last_execution < 5000000:
        return 70000
    if last_execution < 7000000:
        return 100000
    if last_execution < 10000000:
        return 150000
    if last_execution < 15000000:
        return 300000
    if last_execution < 20000000:
        return 400000
    if last_execution < 30000000:
        return 500000
    if last_execution < 50000000:
        return 700000
    return 1000000


def get_price_limit(last_execution):
    if last_execution < 100:
        return 30
    if last_execution < 200:
        return 50
    if last_execution < 500:
        return 80
    if last_execution < 700:
        return 100
    if last_execution < 1000:
        return 150
    if last_execution < 1500:
        return 300
    if last_execution < 2000:
        return 400
    if last_execution < 3000:
        return 500
    if last_execution < 5000:
        return 700
    if last_execution < 7000:
        return 1000
    if last_execution < 10000:
        return 1500
    if last_execution < 15000:
        return 3000
    if last_execution < 20000:
        return 4000
    if last_execution < 30000:
        return 5000
    if last_execution < 50000:
        return 7000
    if last_execution < 70000:
        return 10000
    if last_execution < 100000:
        return 15000
    if last_execution < 150000:
        return 30000
    if last_execution < 200000:
        return 40000
    if last_execution < 300000:
        return 50000
    if last_execution < 500000:
        return 70000
    if last_execution < 700000:
        return 100000
    if last_execution < 1000000:
        return 150000
    if last_execution < 1500000:
        return 300000
    if last_execution < 2000000:
        return 400000
    if last_execution < 3000000:
        return 500000
    if last_execution < 5000000:
        return 700000
    if last_execution < 7000000:
        return 1000000
    if last_execution < 10000000:
        return 1500000
    if last_execution < 15000000:
        return 3000000
    if last_execution < 20000000:
        return 4000000
    if last_execution < 30000000:
        return 5000000
    if last_execution < 50000000:
        return 7000000
    return 10000000


def get_ms_warrant_history(stock_code):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'max-age=0'
    }

    session = KaniRequests(headers=headers)
    result = session.get("https://docs.google.com/spreadsheets/d/e/2PACX-1vQ-SPWgeUiBs8pcrj9vFxYI7-9srSjfy2JDSoJ2-gZ4-bqhCltL2qvzZ2AMkNV7xZ72GH9_jnWqfHM0/pubhtml/sheet?headers=false&gid=0")
    table = result.html.find("table")[0]
    df = pd.read_html(table.raw_html.decode("utf8"), skiprows=4)[0]
    df = df.iloc[:, 1:4]
    df.columns = ["published_date", "stock_code", "name"]
    return df[df["stock_code"] == str(stock_code)]
