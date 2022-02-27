"""
coinbase API client and custom objects.
"""
import json
import os
import pandas as pd
import json
import datetime

from coinbase.wallet.client import Client


class CB:

    """
    Interface to the Coinbase python API.

    Note:
        Requires an API Key and API Secret stored in `coinbase.json`.
        The permissions required to run this code are *read-only* and are the following.

        - ```wallet:sells:read```
        - ```wallet:accounts:read```
        - ```wallet:deposits:read```
        - ```wallet:orders:read```
        - ```wallet:trades:read```
        - ```wallet:transactions:read```
        - ```wallet:user:read```

    Arguments:
		configuration (:obj:`surfingcrypto.config.config`): package configuration object

    Attributes: 
    	configuration (:obj:`surfingcrypto.config.config`): package configuration object
        client (:obj:`coinbase.wallet.client.Client`): client object for making requests to coinbase API
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

    def _get_paginated_items(self, api_method, limit=100):
        """Generic getter for paginated items
        - https://stackoverflow.com/questions/44351034/pagination-on-coinbase-python-api
        """
        all_items = []
        starting_after = None
        while True:
            items = api_method(limit=limit, starting_after=starting_after)
            if items.pagination.next_starting_after is not None:
                starting_after = items.pagination.next_starting_after
                all_items += items.data
            else:
                all_items += items.data
                break
        return all_items

    def _get_accounts(self, limit=100):
        """
        get all accounts through pagination.
        """
        return self._get_paginated_items(self.client.get_accounts, limit=100)

    def _get_transactions(self, account, limit=100):
        """
        get all transaction from specified account through pagination.
        
        Arguments
            account (:obj:`coinbase.wallet.model.ApiObject`) : coinbase account object.
        """
        return self._get_paginated_items(account.get_transactions, limit)

    def get_active_accounts(self):
        """
        get active accounts (balance > 0)

        Return:
            active (:obj:`list` of :obj:`coinbase.ApiObject`): list of coinbase accounts
        """
        active = []
        accounts = self._get_accounts()
        for account in accounts:
            if account["native_balance"]["amount"] != "0.00":
                active.append(account)
        return active

    def get_all_accounts_with_transactions(self, verbose=False):
        """
        get all accounts with recorded transactions.
        
        Note:
            SUPER FUCKING SLOW!!!

        Params:
            verbose (bool): verbose mode in order to check status
        
        Return:
            has_transactions (:obj:`list` of :obj:`coinbase.ApiObject`): list of coinbase accounts
            timeranges (:obj:`list` of :obj:`dict`): list of dictionaries with dates of first and last transaction for each account in `has_transactions`
        """
        has_transactions = []
        timeranges = []
        accounts = self._get_accounts()
        l = len(accounts)
        for account, i in zip(accounts, range(l)):
            if verbose:
                print(f"## {i+1} of {l}")
                print(account["currency"])
            transactions = self._get_transactions(account)
            if len(transactions) > 0:
                timerange = {
                    0: transactions[0]["created_at"],
                    1: transactions[-1]["created_at"],
                }
                has_transactions.append(account)
                timeranges.append(timerange)
        return has_transactions, timeranges

    def get_accounts_from_list(self, l=None):
        """
        gets accounts from a list dumped locally in the config folder.

        Return:
            from_list (:obj:`list` of :obj:`coinbase.ApiObject`): list of coinbase accounts
        """
        if isinstance(l, list):
            from_list = []
            for account in l:
                from_list.append(self.client.get_account(account["account_id"]))
        else:
            raise ValueError("Must be a list.")
        return from_list


class MyCoinbase(CB):
    """
    This class is the user's Coinbase.

    It stores all cryptocurrency accounts - either active or historic.

    It inherits from `surfingcrypto.coinbase.CB` the client methods and all information regarding the user.
    It automatically dumps temporary data in order to load accounts faster.

    Arguments:
        active_accounts (bool) : default `True`, select active (balance>0) accounts only.
        force (bool): force update from API even if local cache is found.
        configuration (:obj:`surfingcrypto.config.config`) : package configuration object.

    Attributes:
        accounts (:obj:`list` of :obj:`coibase.model.ApiObject`): list of selected accounts.
        last_updated (:obj:`datetime.datetime`): datetime of last updates of account list.
        timeranges (:obj:`list` of :obj:`dict`): list of dictionaries with dates of first and last transaction for each account
        isHistoric (bool): if module has been loaded in historic mode.
        json_path (str): path to json dump file

    """

    def __init__(self, active_accounts=True,force=False, *args, **kwargs):
        super(MyCoinbase, self).__init__(*args, **kwargs)
        self.start(active_accounts,force)
        return

    def start(self, active_accounts,force):
        """
        start MyCoinbase module, loading accounts as specified.

        Arguments:
            active_accounts (bool): get only active (balance>0) accounts 
            force (bool): force update from API even if local cache is found.
        """
        self.json_path = self.configuration.config_folder + "/coinbase_accounts.json"

        if active_accounts:
            self.accounts = self.get_active_accounts()
            self.isHistoric = False
            self.last_updated=datetime.datetime.utcnow()
        elif active_accounts is False:
            self.isHistoric = True
            if os.path.isfile(self.json_path) and not force:
                accounts, last_updated = self._load_accounts()
                self.last_updated = datetime.datetime.strptime(last_updated,"%Y-%m-%dT%H:%M:%SZ")
                if datetime.datetime.utcnow() - self.last_updated < datetime.timedelta(days=7):
                    self.accounts = self.get_accounts_from_list(accounts)
                else:
                    (
                        self.accounts,
                        self.timeranges,
                    ) = self.get_all_accounts_with_transactions()
                    self._dump_accounts()
            else:
                (
                    self.accounts,
                    self.timeranges,
                ) = self.get_all_accounts_with_transactions()
                self._dump_accounts()
                self.last_updated=datetime.datetime.utcnow()
        else:
            raise ValueError("Either true or false.")

    def _dump_accounts(self):
        """
        dumps fetched accounts for faster execution time in following sessions.
        """
        l = []
        for account, timerange in zip(self.accounts, self.timeranges):
            l.append(
                {
                    "currency": account["currency"],
                    "account_id": account["id"],
                    "balance": account["balance"]["amount"],
                    "timerange": timerange,
                }
            )
        dump = {
            "datetime": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "accounts": l,
        }
        with open(self.json_path, "w") as f:
            json.dump(dump, f, indent=4,default=str)

    def _load_accounts(self):
        """
        load accounts from dumped `coinbase_accounts.json` file.
        """
        with open(self.json_path, "rb") as f:
            dict = json.load(f)
            accounts = dict["accounts"]
            last_updated = dict["datetime"]
        return accounts, last_updated

    def mycoinbase_report(self):
        """
        nicely formatted report of accounts portfolio and user's total balance in EUR
        
        Returns:
            s (str): text
        """
        s = ""
        tot = 0
        if hasattr(self, "accounts"):
            for account in self.accounts:
                if float(account.native_balance.amount) > 0:
                    s = (
                        s
                        + str(account.currency)
                        + " : "
                        + str(account.native_balance)
                        + "\n"
                    )
                    tot += float(account.native_balance.amount)
            s = s + "---\n" + "Portfolio: EUR " + "{:.2f}".format(tot)
            return s
        else:
            raise ValueError("Must get accounts first.")

    def __repr__(self):
        return f"MyCoinbase( isHistoric:{self.isHistoric}, last_updated:{self.last_updated}, N_accounts:{len(self.accounts)})"

    def __str__(self):
        return f"MyCoinbase( isHistoric:{self.isHistoric},  last updated:{self.last_updated}, N_accounts:{len(self.accounts)})"


class TransactionsGetter:
    """
    This objects fetches all coinbase transactions and parses them into a known format.

    Arguments:
        mycoinbase (:obj:`surfingcrypto.coinbase.coinbase.MyCoinbase`): :obj:`MyCoinbase` object.

    Attributes:
        known_types (list): list of string names of supported transaction types.
        mycoinbase (:obj:`surfingcrypto.coinbase.coinbase.MyCoinbase`): :obj:`MyCoinbase` object.
        df (:obj:`pandas.DataFrame`): dataframe of all known transactions
        transactions (:obj:`list` of :obj:`coibase.model.ApiObject`): list of processed transactions.
        unhandled_trans (:obj:`list` of :obj:`dict`): list informations of unhandled transactions.
        error_log (:obj:`list` of :obj:`dict`): list informations of transactions that resulted in an error.
    """

    def __init__(self, mycoinbase):
        self.mycoinbase = mycoinbase
        self.load()

    def load(self):
        if self.mycoinbase.isHistoric is True:
            ### ci sonotanti tipi di transactions
            self.unhandled_trans = []
            # error log for when failing handling known transactions types
            self.error_log = []

            self.df = []
            self.transactions = []

            if hasattr(self.mycoinbase, "accounts"):
                for account in self.mycoinbase.accounts:
                    self.handle_transactions(account)
                self.df = pd.DataFrame(self.df).set_index("datetime")
                order = ["type", "amount", "symbol", "native_amount", "nat_symbol"]
                neworder = order + [c for c in self.df.columns if c not in order]
                self.df = self.df.reindex(columns=neworder)
            else:
                raise ValueError("MyCoinbase objects must have an accounts attribute.")

            if len(self.unhandled_trans) > 0:
                print(
                    f"Warning! There are {len(self.unhandled_trans)} unknown transaction types and therefore they have been skipped."
                )
            if len(self.error_log) > 0:
                print(
                    f"Warning! There were {len(self.error_log)} errors during the handling of transactions."
                )
        else:
            raise ValueError("Must load historic data.")

    def handle_transactions(self, account):
        """
        handles the transactions based on type.
        """
        self.known_types = [
            "buy",
            "sell",
            "trade",
            "send",
            "fiat_withdrawal",
            "fiat_deposit",
        ]
        for transaction in self.mycoinbase._get_transactions(account):
            try:
                if transaction["type"] in self.known_types:
                    self.process_transaction(account, transaction)
                    self.transactions.append(transaction)
                else:
                    self.unhandled_trans.append(
                        {
                            "transaction_type": transaction["type"],
                            "account_id": account["id"],
                            "transaction_id": transaction["id"],
                        }
                    )
            except Exception as e:
                symbol, amount, datetime = self.get_transact_info(transaction)
                self.error_log.append(
                    {
                        "transaction_type": transaction["type"],
                        "account_id": account["id"],
                        "transaction_id": transaction["id"],
                        "info": {"amount": amount, "symbol": symbol, "date": datetime},
                        "error_log": e,
                    }
                )

    def process_transaction(self, account, transaction):
        """
        process a transaction.
        """
        # spot price??
        symbol, amount, datetime = self.get_transact_info(transaction)
        nat_amount, nat_symbol = self.get_native_amount(transaction)
        total, subtotal, total_fee = self.get_transact_data(account, transaction)

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
                "trade_id": trade_id,
            }
        )

    def get_transact_info(self, transaction):
        """
        get basic info from transaction.
        """
        symbol = transaction["amount"]["currency"]
        amount = float(transaction["amount"]["amount"])
        datetime = transaction["created_at"]
        return symbol, amount, datetime

    def get_native_amount(self, transaction):
        """
        gets native amount from transaction
        """
        native_amount = float(transaction["native_amount"]["amount"])
        native_symbol = transaction["native_amount"]["currency"]
        return native_amount, native_symbol

    def get_transact_data(self, account, transaction):
        """
        gets required additional data (eg. fees) from different kinds of transactions.
        """
        if transaction["type"] == "sell":
            t = self.mycoinbase.client.get_sell(
                account["id"], transaction["sell"]["id"]
            )
        elif transaction["type"] == "buy":
            t = self.mycoinbase.client.get_buy(account["id"], transaction["buy"]["id"])
        elif transaction["type"] == "fiat_withdrawal":
            t = self.mycoinbase.client.get_withdrawal(
                account["id"], transaction["fiat_withdrawal"]["id"]
            )
        elif transaction["type"] == "fiat_deposit":
            t = self.mycoinbase.client.get_deposit(
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

