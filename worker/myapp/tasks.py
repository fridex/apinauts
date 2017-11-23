#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ######################################################################
# Copyright (C) 2016-2017  Fridolin Pokorny, fridolin.pokorny@gmail.com
# This file is part of Selinon project.
# ######################################################################

import requests
from selinon import SelinonTask


class RetrieveTransactionsTask(SelinonTask):
    URL = "https://www.csast.csas.cz/webapi/api/v3/netbanking/my/transactions"
    TOKEN = '3/DywBVF9tnpveEcnn6qi4qYy7tsCgUCY4j24Splh021Pp535WilPGzj66FAwtaZLh'
    API_KEY = "4b8d5c6b-2101-464b-a987-0571f8ead003"

    @staticmethod
    def clear_transaction(transaction):
        return {
            "id": transaction.get("id"),
            "title": transaction.get("title"),
            "cardTransaction": transaction.get("cardId") is not None,
            "receiverIBAN": transaction.get("receiver").get("iban"),
            "direction": "IN" if transaction.get("txDirection") == "INCOMING" else "OUT",
            "amount": transaction.get("amount").get("value") / 10 ** transaction.get("amount").get("precision")
        }

    @classmethod
    def get_transactions(cls, url, token, api_key, page=None):
        result = []
        next_page = None

        if page:
            url = "%s?page=%d" % (url, page)
        req = requests.request("GET", url, headers={"web-api.key": api_key, "Authorization": "Bearer %s" % token})
        req.raise_for_status()
        data = req.json()

        if data.get("currentPage") < data.get("totalPages", 0) - 1:
            next_page = data.get("currentPage", 0) + 1

        if data.get("collection"):
            for t in data.get("collection"):
                result.append(cls.clear_transaction(t))

        return result, next_page

    def run(self, node_args):
        page = 0
        result = []
        while page is not None:
            data, page = self.get_transactions(self.URL, self.TOKEN, self.API_KEY, page)
            result += data

        return result
