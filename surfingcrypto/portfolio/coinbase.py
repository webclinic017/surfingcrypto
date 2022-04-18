"""
coinbase API client and custom objects.
"""
import json
import os
import pandas as pd
import datetime as dt
import pickle

from coinbase.wallet.client import Client


class CB:

    """
    Interface to the Coinbase python API.

    Note:
        Requires an API Key and API Secret stored in `coinbase.json`.
        The permissions required to run this code are *read-only* and are the
        following.

        - ```wallet:sells:read```
        - ```wallet:accounts:read```
        - ```wallet:deposits:read```
        - ```wallet:orders:read```
        - ```wallet:trades:read```
        - ```wallet:transactions:read```
        - ```wallet:user:read```

    Arguments:
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object

    Attributes:
        configuration (:obj:`surfingcrypto.config.config`): package
            configuration object
        client (:obj:`coinbase.wallet.client.Client`): client object for
            making requests to coinbase API
        user (:obj:`coinbase API object`): user API object
    """

    def __init__(self, configuration):

        if hasattr(configuration, "coinbase"):
            self.configuration = configuration
            self.client = Client(
                configuration.coinbase["key"], configuration.coinbase["scrt"]
            )
            self.user = self.client.get_current_user()
        else:
            raise ValueError("config.json file must contain a coinbase token.")

    def _filter_paginated_items(
        self, api_method, account: str, filter=dict or None, limit=2
    ):
        """
        filter the reponse for updating data using a cached dict.
        """
        all_items = []
        starting_after = None
        while True:
            items = api_method(limit=limit, starting_after=starting_after)
            if items.pagination.next_starting_after is not None:
                starting_after = items.pagination.next_starting_after
                all_items += self._filter_by_cache(items.data, filter, account)
                if len(all_items) < len(items.data):
                    break
            else:
                all_items += self._filter_by_cache(items.data, filter, account)
                break
        return all_items

    def _filter_by_cache(self, data: list, filter: dict or None, account: str):
        # this filter works as the transactions are returned in chronological order
        if filter is not None:
            new_items = []
            for item in data:
                if (
                    item["id"]
                    == filter["accounts"][account]["last_transaction_id"]
                ):
                    return new_items
                else:
                    new_items.append(item)
        else:
            return data

    def _get_accounts(self, limit=100):
        """
        get all accounts through pagination.
        """
        return self._filter_paginated_items(
            self.client.get_accounts, None, filter=None, limit=100
        )

    def get_active_accounts(self):
        """
        get active accounts (balance > 0)

        Return:
            active (:obj:`list` of :obj:`coinbase.ApiObject`): list of
                coinbase accounts
        """
        active = []
        accounts = self._get_accounts()
        for account in accounts:
            if account["native_balance"]["amount"] != "0.00":
                active.append(account)
        return active

    def _get_transactions(self, account, cache=None):
        """
        get transaction from specified account through pagination.
        if provided with 

        Arguments
            account (:obj:`coinbase.wallet.model.ApiObject`) : coinbase
                account object.
            cache (_type_) : _descr_
        """
        return self._filter_paginated_items(
            account.get_transactions, account["currency"], cache, limit=5
        )

    def get_full_history(self, cache: None or dict, transactions=[]) -> tuple:
        """
        get all accounts with recorded transactions.

        From v0.2 features updating accounts and transactions from cache.

        Args:
            cache (None or dict): _description_
            transactions (list, optional): _description_. Defaults to [].

        Returns:
            tuple: _description_
        """
        has_transactions = []
        new_transactions = []
        account_responses = {}

        accounts = self._get_accounts()

        for account in accounts:

            has_activity = account["created_at"] != account["updated_at"]

            if has_activity:
                # get transactions, either all or updating from cache
                if (
                    cache is None  # no cache available or force
                    or account["currency"]
                    not in cache["accounts"].keys()  # not present in cache
                ):
                    new_account_transactions = self._get_transactions(account)
                    update = False
                else:
                    new_account_transactions = self._get_transactions(
                        account, cache
                    )
                    update = True

                if len(new_account_transactions) > 0 or update is True:
                    # save account
                    has_transactions.append(account)

                    # all known account transactions for finding the latest response info
                    account_transactions = new_account_transactions + [
                        x
                        for x in transactions
                        if x["amount"]["currency"] == account["currency"]
                    ]
                    account_responses[
                        account["currency"]
                    ] = self._fmt_account_response(
                        account, account_transactions
                    )

                    # append transactions
                    new_transactions = (
                        new_transactions + new_account_transactions
                    )

        return (
            has_transactions,
            (new_transactions + transactions),
            account_responses,
        )

    def _fmt_account_response(self, account, transactions: list):

        """_summary_

        Args:
            account (wallet.model.ApiObject): _description_
            transactions (list): _description_

        Returns:
            dict: _description_
        """
        return {
            "currency": account["currency"],
            "account_id": account["id"],
            "active": "True"
            if float(account["balance"]["amount"]) > 0
            else "False",
            "last_transaction_id": transactions[0]["id"],
            "timerange": {
                0: transactions[0]["created_at"],
                1: transactions[-1]["created_at"],
            },
        }


class MyCoinbase(CB):
    """
    This class is the user's Coinbase account.

    It stores all cryptocurrency accounts - either active or historic.

    It inherits from `surfingcrypto.coinbase.CB` the client methods
    and all information regarding the user.
    It automatically dumps temporary data in order to load accounts faster.

    Arguments:
        active_accounts (bool) : default `True`, select
            active (balance>0) accounts only. Defaults to True.
        force (bool): force update from API even if
            local cache is found. Defaults to False.
        configuration (:obj:`surfingcrypto.config.config`) : package
            configuration object.

    Attributes:
        accounts (:obj:`list` of :obj:`coibase.model.ApiObject`):
            list of selected accounts.
        transactions (:obj:`list` of :obj:`coibase.model.ApiObject`): 
            list of transactions.
        active_accounts (list): list of string names of active accounts (balance>0.00)
        history (:obj:`surfingcrypto.portfolio.coinbase.TransactionsHistory`):
            `TransactionsHistory` object
        isHistoric (bool): if module has been loaded in historic mode,
            a.k.a. all accounts with a transaction in the record
        json_path (str): path to json dump file

    """

    def __init__(self, active_accounts=True, force=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start(active_accounts, force)
        self._set_active_accounts()
        return

    def start(self, active_accounts: bool, force: bool):
        """
        start MyCoinbase module, loading accounts as specified.

        Arguments:
            active_accounts (bool): get only active (balance>0) accounts
            force (bool): force update from API even if local cache is found.
        """
        self.json_path = (
            self.configuration.config_folder + "/coinbase_accounts.json"
        )
        self.pickle_path = (
            self.configuration.config_folder + "/coinbase_transactions"
        )

        cache = None
        self.transactions = []

        if active_accounts:
            self.accounts = self.get_active_accounts()
            self.isHistoric = False
        else:
            self.isHistoric = True
            # if cache is found, use it
            if (
                os.path.isfile(self.json_path)
                and os.path.isfile(self.pickle_path)
                and not force
            ):
                cache, self.transactions = self._load_cache()
            # get data
            (
                self.accounts,
                self.transactions,
                responses,
            ) = self.get_full_history(cache, self.transactions)
            self._dump_cache(responses)

    def _dump_cache(self, responses: dict):
        """
        dumps a dict for accounts and and a pickle object for transactions,
        for faster execution time in following sessions.

        """
        dict = {
            "datetime": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "accounts": responses,
        }
        with open(self.json_path, "w") as f:
            json.dump(dict, f, indent=4, default=str)
        with open(self.pickle_path, "wb") as f2:
            pickle.dump(self.transactions, f2)

    def _load_cache(self) -> dict and list:
        """
        load accounts and transactions from dumped cache

        Returns:
            dict and list: _description_
        """
        with open(self.json_path, "rb") as f:
            dict = json.load(f)
        # format datetime
        dict["datetime"] = dt.datetime.strptime(
            dict["datetime"], "%Y-%m-%dT%H:%M:%SZ"
        )

        with open(self.pickle_path, "rb") as f2:
            transactions = pickle.load(f2)
        return dict, transactions

    def _set_active_accounts(self):
        """
        sets the currently active accounts, a.k.a. balance >0
        this is required for the case when the module is loaded in historic mode, 
        so to distinguish active accounts from all known accounts.
        """
        active = []
        if hasattr(self, "accounts"):
            for account in self.accounts:
                if float(account.native_balance.amount) > 0:
                    active.append(account.currency)
        self.active_accounts = active

    def get_history(self):
        """
        start a TransactionsHistory object
        """
        self.history = TransactionsHistory(self)
        pass

    def __repr__(self):
        return (
            f"MyCoinbase( isHistoric:{self.isHistoric},"
            f" N_accounts:{len(self.accounts)})"
        )

    def __str__(self):
        return (
            f"MyCoinbase( isHistoric:{self.isHistoric},"
            f" N_accounts:{len(self.accounts)})"
        )


class TransactionsHistory:
    """
    This objects fetches all coinbase transactions and parses them into a
    known format.

    Arguments:
        mycoinbase (:obj:`surfingcrypto.coinbase.coinbase.MyCoinbase`):
            :obj:`MyCoinbase` object.

    Attributes:
        df (:obj:`pandas.DataFrame`): dataframe of all known transactions
        processed_transactions (:obj:`list` of :obj:`coibase.model.ApiObject`): list
            of processed transactions.
        known_types (list): list of string names
            of supported transaction types.
        unhandled_trans (:obj:`list` of :obj:`dict`): list informations of
            unhandled transactions.
        errors (:obj:`list` of :obj:`coibase.model.ApiObject`): list of 
            transactions that resulted in an error
        error_log (:obj:`list` of :obj:`dict`): list informations of
            transactions that resulted in an error.
    """

    def __init__(self, mycoinbase):
        self._mycoinbase = mycoinbase
        self.known_types = [
            "buy",
            "sell",
            "trade",  # verify
            "send",  # verify
            "fiat_withdrawal",
            "fiat_deposit",
        ]
        self._start()

    def _start(self):
        if self._mycoinbase.isHistoric is True:
            # ci sonotanti tipi di transactions
            self.unhandled_trans = []
            # error log for when failing handling known transactions types
            self.error_log = []
            self.errors = []

            self.df = []
            self.processed_transactions = []

            if hasattr(self._mycoinbase, "accounts"):
                for account in self._mycoinbase.accounts:
                    self._handle_transactions(account)
                self.df = pd.DataFrame(self.df).set_index("datetime")
                self.df.sort_index(inplace=True)
                order = [
                    "type",
                    "amount",
                    "symbol",
                    "native_amount",
                    "nat_symbol",
                ]
                neworder = order + [
                    c for c in self.df.columns if c not in order
                ]
                self.df = self.df.reindex(columns=neworder)
            else:
                raise ValueError(
                    "MyCoinbase objects must have an accounts attribute."
                )
        else:
            raise ValueError("Must load historic data.")

    def _handle_transactions(self, account):
        """
        handles the transactions based on type.
        """
        for transaction in self._mycoinbase.transactions:
            if transaction["amount"]["currency"] == account["currency"]:
                if transaction["type"] in self.known_types:
                    self._process_transaction(account, transaction)
                else:
                    self.unhandled_trans.append(
                        {
                            "transaction_type": transaction["type"],
                            "account_id": account["id"],
                            "transaction_id": transaction["id"],
                        }
                    )

    def _process_transaction(self, account, transaction):
        """
        process a transaction.
        """
        # spot price??
        symbol, amount, datetime, id = self._get_transact_info(transaction)
        nat_amount, nat_symbol = self._get_native_amount(transaction)
        total, subtotal, total_fee = None, None, None
        try:
            total, subtotal, total_fee = self._get_transact_data(
                account, transaction
            )
            self.processed_transactions.append(transaction)

        except Exception as e:
            self.errors.append(transaction)
            self.error_log.append(
                {
                    "transaction_type": transaction["type"],
                    "account_id": account["id"],
                    "transaction_id": transaction["id"],
                    "info": {
                        "amount": amount,
                        "symbol": symbol,
                        "date": datetime,
                    },
                    "error_log": e,
                }
            )

        if subtotal is None:
            spot_price = nat_amount / amount
        else:
            spot_price = subtotal / amount

        if transaction["type"] == "trade":
            trade_id = transaction["trade"]["id"]
        else:
            trade_id = None

        self.df.append(
            {
                "type": transaction["type"],
                "datetime": datetime,
                "symbol": symbol,
                "amount": amount,
                "native_amount": nat_amount,
                "nat_symbol": nat_symbol,
                "total": total,
                "subtotal": subtotal,
                "total_fee": total_fee,
                "spot_price": abs(spot_price),
                "transaction_id": id,
                "trade_id": trade_id,
            }
        )

    def _get_transact_info(self, transaction):
        """
        get basic info from transaction.
        """
        symbol = transaction["amount"]["currency"]
        amount = float(transaction["amount"]["amount"])
        datetime = transaction["created_at"]
        id = transaction["id"]
        return symbol, amount, datetime, id

    def _get_native_amount(self, transaction):
        """
        gets native amount from transaction
        """
        native_amount = float(transaction["native_amount"]["amount"])
        native_symbol = transaction["native_amount"]["currency"]
        return native_amount, native_symbol

    def _get_transact_data(self, account, transaction):
        """
        gets required additional data (eg. fees)
        from different kinds of transactions.
        """
        if transaction["type"] == "sell":
            t = self._mycoinbase.client.get_sell(
                account["id"], transaction["sell"]["id"]
            )
        elif transaction["type"] == "buy":
            t = self._mycoinbase.client.get_buy(
                account["id"], transaction["buy"]["id"]
            )
        elif transaction["type"] == "fiat_withdrawal":
            t = self._mycoinbase.client.get_withdrawal(
                account["id"], transaction["fiat_withdrawal"]["id"]
            )
        elif transaction["type"] == "fiat_deposit":
            t = self._mycoinbase.client.get_deposit(
                account["id"], transaction["fiat_deposit"]["id"]
            )
        elif transaction["type"] in ["send", "trade"]:
            t = None
        else:
            raise ValueError("missing specification in source code.")

        if t is not None:
            if transaction["type"] in ["fiat_deposit", "fiat_withdrawal"]:
                # in these two transactions `total` is not present
                total = float(t["amount"]["amount"])
            else:
                total = float(t["total"]["amount"])
            subtotal = float(t["subtotal"]["amount"])
            total_fee = 0
            if "fees" in t:
                for fee in t["fees"]:
                    total_fee += float(fee["amount"]["amount"])
        else:
            total, subtotal, total_fee = None, None, None
        return total, subtotal, total_fee

    def __repr__(self):
        return (
            f"TransactionsHistory("
            f"Transactions:{len(self.processed_transactions)+len(self.unhandled_trans)+len(self.error_log)} "
            f"- Processed:{len(self.df)}, "
            f"Unhandled:{len(self.unhandled_trans)} "
            f"- Errors:{len(self.error_log)}"
            ")"
        )

    def __str__(self):
        return (
            f"TransactionsHistory("
            f"Transactions:{len(self.processed_transactions)+len(self.unhandled_trans)+len(self.error_log)} "
            f"- Processed:{len(self.df)}, "
            f"Unhandled:{len(self.unhandled_trans)} "
            f"- Errors:{len(self.error_log)}"
            ")"
        )

    def executed_without_errors(self) -> bool:
        """
        check if the object was executed with errors

        Returns:
            bool: execution resulted in errors
        """
        if len(self.unhandled_trans) + len(self.error_log) > 0:
            return False
        else:
            return True
