#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ######################################################################
# Copyright (C) 2016-2017  Fridolin Pokorny, fridolin.pokorny@gmail.com
# This file is part of Selinon project.
# ######################################################################

import logging
import requests
from selinon import SelinonTask

logger = logging.getLogger(__name__)

class RetrieveTransactionsTask(SelinonTask):
    URL = "https://www.csast.csas.cz/webapi/api/v3/netbanking/my/transactions"
    TOKEN = '3/3UNLfw0XRkzTqz47DrnNcuxDSevw1T3pSeO665q7LKFbOjEIRynb3djsYA5y6fAI'
    API_KEY = "4b8d5c6b-2101-464b-a987-0571f8ead003"

    @staticmethod
    def clear_transaction(transaction):
        result = {
            "id": transaction.get("id"),
            "title": transaction.get("title"),
            "cardTransaction": transaction.get("cardId") is not None,
            "amount": transaction.get("amount").get("value") / 10 ** transaction.get("amount").get("precision"),
            "currency": transaction.get("amount").get("currency")
        }

        if result.get("amount") > 0:
            result["secondParty"] = transaction.get("senderName")
        else:
            result["secondParty"] = transaction.get("receiverName")

        return result

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

        return {
            'added': self.storage.store_transactions(result)
        }


class AssignCategoryTask(SelinonTask):
    def run(self, node_args):
        for bank_id in node_args.get('added', []):
            transaction = self.storage.get_transaction_by_bank_id(bank_id)

            already_stored = self.storage.get_transactions_by_title(transaction.title)
            suggested_category = None
            for entry in already_stored:
                if entry.bank_transaction_id in node_args['added']:
                    # Ignore new transactions
                    continue

                if not entry.category:
                    break

                if suggested_category and suggested_category != entry.category:
                    suggested_category = None
                    break

                suggested_category = entry.category

            if suggested_category:
                transaction.category = suggested_category
                try:
                    self.storage.session.ad(transaction)
                    logger.info("Assigned category for transaction %r: %r",
                                transaction.bank_transaction_id, transaction.category)
                except:
                    self.storage.session.rollback()
                    logger.exception("Failed to modify suggested category %r", suggested_category)
