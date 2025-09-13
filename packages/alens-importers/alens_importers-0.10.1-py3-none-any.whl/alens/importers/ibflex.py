"""
Creating IBKR importer from scratch.
"""

from collections import defaultdict
import os
import re
import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Tuple

import beangulp  # type: ignore
from beancount.core import amount, data, flags, position, realization
from beangulp import cache
from beangulp.importers.mixins.identifier import identify
import ibflex
from ibflex import TradeType, Types
from ibflex.enums import BuySell, CashAction, OpenClose, Reorg
from loguru import logger

import alens.importers.dedup
from alens.importers.utilities import get_number_of_decimal_places


class AccountTypes(str, Enum):
    """Account types in the configuration file"""

    CASH = "cash_account"
    STOCK = "stock_account"
    DIVIDEND = "dividend_account"
    INTEREST = "interest_account"
    CAPGAIN = "capgain_account"
    BRKINT = "broker_interest_account"
    FEES = "fees_account"
    TXFER = "txfer-{currency}"
    WHTAX = "whtax_account"


class Importer(beangulp.Importer):
    """IBKR Flex Query XML importer for Beancount"""

    def __init__(self, *args, **kwargs):
        logger.debug("Initializing IBKR importer")

        # get config, the first argument.
        self.config = args[0]

        self.holdings_map = defaultdict(list)
        # self.use_existing_holdings = True
        self.use_existing_holdings = False

        # create symbol dictionaries.
        symbols = self.config.get("symbols")
        self.symbol_to_isin, self.isin_to_symbol = self.create_symbol_dictionaries(
            symbols
        )

        super().__init__(**kwargs)

    @property  # type: ignore
    def name(self) -> str:
        logger.debug("Getting importer name")

        return "AS IBKR importer (new)"

    def identify(self, filepath: str) -> bool:
        """Indicates whether the importer can handle the given file"""
        logger.debug(f"Identifying {filepath}")

        matchers = {
            # File is xml
            "mime": [re.compile(r"text/xml")],
            # The main XML tag is FlexQueryResponse
            "content": [re.compile(r"<FlexQueryResponse ")],
        }

        return identify(matchers, None, cache.get_file(filepath))

    def account(self, filepath: str) -> data.Account:
        """Return the archiving account associated with the given file."""
        # TODO : return the correct account?
        return "ibkr"

    def filename(self, filepath: str) -> Optional[str]:
        """Returns the archival filename for the report"""
        return os.path.basename(filepath)

    def extract(self, filepath: str, existing: data.Entries) -> data.Entries:
        """
        Extract transactions and other directives from a document.
        Existing entries are received as an argument, if Beancount file was
        specified.
        Deduplication is done against these.
        A list of imported directives should be returned.
        """
        logger.debug(f"Extracting from {filepath}")

        if self.use_existing_holdings and existing is not None:
            self.holdings_map = self.get_holdings_map(existing)
        else:
            self.holdings_map = defaultdict(list)
        statements = ibflex.parser.parse(open(filepath, "r", encoding="utf-8"))
        assert isinstance(statements, Types.FlexQueryResponse)

        statement = statements.FlexStatements[0]
        assert isinstance(statement, Types.FlexStatement)

        transactions = (
            self.trades(statement.Trades)
            + self.cash_transactions(statement.CashTransactions)
            + self.cash_balances(statement.CashReport)
            + self.corporate_actions(statement.CorporateActions)
            + self.stock_balances(statement.OpenPositions, statement)
        )

        transactions = self.merge_dividend_and_withholding(transactions)
        transactions = self.merge_forex(transactions)
        transactions = self.merge_trades(transactions)
        # TODO: check this
        # # self.adjust_closing_trade_cost_basis(transactions)
        # return self.autoopen_accounts(transactions, existing_entries) + transactions
        self.cleanup_metadata_tags(transactions)

        return transactions

    def create_symbol_dictionaries(
        self, symbols: list[Tuple[str, str]]
    ) -> Tuple[dict, dict]:
        """
        Create symbol dictionaries, to fetch Symbols/ISINs
        Reads array of tuples of (symbol, isin), or array of arrays.
        """
        symbol_to_isin = {}
        isin_to_symbol = {}

        # 2. Populate the dictionaries from your list
        for symbol, isin in symbols:
            symbol_to_isin[symbol] = isin
            isin_to_symbol[isin] = symbol

        return symbol_to_isin, isin_to_symbol

    def get_account_name(self, acct_type: AccountTypes, symbol=None, currency=None):
        """Get the account name from the config file"""
        # Apply values to the template.
        if currency is not None:
            acct_type_string = acct_type.value.replace("{currency}", currency)
        else:
            acct_type_string = acct_type.value

        account_name = self.config.get(acct_type_string)
        if account_name is None:
            raise ValueError(f"Account name not found for '{acct_type_string}'")
        assert isinstance(account_name, str)

        # Populate template fields.
        if symbol is not None:
            account_name = account_name.replace("{symbol}", symbol.replace(" ", ""))
        if currency is not None:
            account_name = account_name.replace("{currency}", currency)
        return account_name

    def cash_transactions(self, ct):
        """Extract cash transactions"""
        transactions = []
        for index, row in enumerate(ct):
            if row.type == CashAction.DEPOSITWITHDRAW:
                transactions.append(self.deposit_from_row(index, row))
            elif row.type in (CashAction.BROKERINTRCVD, CashAction.BROKERINTPAID):
                transactions.append(self.interest_from_row(index, row))
            elif row.type in (CashAction.FEES, CashAction.COMMADJ):
                transactions.append(self.fee_from_row(index, row))
            elif row.type in (
                CashAction.WHTAX,
                CashAction.DIVIDEND,
                CashAction.PAYMENTINLIEU,
            ):
                transactions.append(
                    self.dividends_and_withholding_tax_from_row(index, row)
                )
            else:
                raise RuntimeError(f"Unknown cash transaction type: {row.type}")

        return transactions

    def deposit_from_row(self, idx, row):
        amount_ = amount.Amount(row.amount, row.currency)
        postings = [
            data.Posting(
                self.get_account_name(AccountTypes.CASH, currency=row.currency),
                amount_,
                None,
                None,
                None,
                None,
            ),
            data.Posting(
                self.get_account_name(AccountTypes.TXFER, currency=row.currency),
                -amount_,
                None,
                None,
                None,
                None,
            ),
        ]
        meta = data.new_metadata("deposit/withdrawal", 0)
        return data.Transaction(
            meta,
            row.reportDate,
            flags.FLAG_OKAY,
            # "self",  # payee
            "IB {currency} Deposit".replace("{currency}", row.currency),
            # row.description,
            None,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def dividends_and_withholding_tax_from_row(self, idx, row: Types.CashTransaction):
        """Converts dividends, payment inlieu of dividends and withholding tax to a
        beancount transaction.
        Stores div type in metadata for the merge step to be able to match tax withdrawals
        to the correct div.
        """
        assert isinstance(row.currency, str)
        assert isinstance(row.amount, Decimal)
        
        # Ensure consistent decimal formatting
        formatted_amount = format_decimal_for_beancount(row.amount)
        
        amount_ = amount.Amount(formatted_amount, row.currency)

        text = row.description
        text = self.groom_dividend_description(text)

        # Find ISIN in description in parentheses
        # isin = re.findall(r"\(([a-zA-Z]{2}[a-zA-Z0-9]{9}\d)\)", text)[0]
        isin = row.isin
        # pershare_match = re.search(r"(\d*[.]\d*)(\D*)(PER SHARE)", text, re.IGNORECASE)
        # payment in lieu of a dividend does not have a PER SHARE in description
        # pershare = pershare_match.group(1) if pershare_match else ""

        # meta = {"isin": isin, "per_share": pershare}
        meta = {"isin": isin}

        account = ""
        payee: str = ""
        type_ = None
        tax_reversal_meta = None

        # Get the beancount symbol, for use in the book.
        b_symbol = self.isin_to_symbol.get(isin)
        #assert isinstance(b_symbol, str)
        if b_symbol is None:
            raise ValueError(f"No symbol found for ISIN {isin}")
        acc_symbol = format_symbol_for_account_name(b_symbol)

        if row.type == CashAction.WHTAX:
            account = self.get_account_name(
                AccountTypes.WHTAX, row.symbol, row.currency
            )
            type_ = CashAction.DIVIDEND

            # If this is a tax reversal, mark it as positive transaction.
            if row.amount > 0:
                meta["div"] = True
                tax_reversal_meta = data.new_metadata(
                    "tax_reversal", 0, {"date": row.dateTime.date()}
                )

        elif row.type == CashAction.DIVIDEND or row.type == CashAction.PAYMENTINLIEU:
            # Check if this is a dividend or interest income.
            dist_accts = self.config.get("interest_symbols")
            if dist_accts and b_symbol in dist_accts:
                account = self.get_account_name(
                    AccountTypes.INTEREST, symbol=acc_symbol
                )
            else:
                account = self.get_account_name(
                    AccountTypes.DIVIDEND, acc_symbol, row.currency
                )

            type_ = row.type
            meta["div"] = True

        meta["div_type"] = type_.value if type_ else None

        postings = [
            data.Posting(
                self.get_account_name(AccountTypes.CASH, row.symbol, row.currency),
                amount_,
                None,
                None,
                None,
                None,
            ),
            data.Posting(account, -amount_, None, None, None, tax_reversal_meta),
        ]
        metadata = data.new_metadata(
            "dividend",
            0,
            meta,
        )

        assert isinstance(row.reportDate, datetime.date)

        # row.dateTime = the effective/book date.
        # row.reportDate = the date when the transaction happened and appeared in the report.

        payee = self.config.get("dividend_payee").replace("{symbol}", b_symbol)

        return data.Transaction(
            metadata,
            # date
            row.reportDate,
            flags.FLAG_OKAY,
            # payee
            payee,
            text,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def groom_dividend_description(self, text) -> str:
        """
        This function is used to remove the redundant info at the beginning of the description
        """
        if not isinstance(text, str):
            return text

        # throw away the redundant info at the beginning
        parts = text.split(" ")
        # find the "DIVIDEND" part and take the remaining text.
        div_location = parts.index("DIVIDEND")
        remaining_parts = parts[div_location + 1 :]
        # print(parts)
        # print(remaining_parts)
        return " ".join(remaining_parts)

    def cleanup_metadata_tags(self, transactions: list[data.Transaction]):
        """
        This function is used to remove the tags that are no longer needed
        """
        # clean up the metadata tags on Transactions
        for t in transactions:
            if isinstance(t, data.Transaction):
                if "div_type" in t.meta:
                    del t.meta["div_type"]
                if "isin" in t.meta:
                    del t.meta["isin"]
                if "div" in t.meta:
                    del t.meta["div"]
                if "descr" in t.meta:
                    del t.meta["descr"]

    def merge_dividend_and_withholding(self, entries):
        """
        This merges together transactions for earned dividends with the witholding tax ones,
        as they can be on different lines in the cash transactions statement.
        """
        grouped = defaultdict(list)
        for e in entries:
            if not isinstance(e, data.Transaction):
                continue
            if "div_type" in e.meta and "isin" in e.meta:
                # Group by date, payee, div_type
                grouped[(e.date, e.payee, e.meta["div_type"])].append(e)
        for group in grouped.values():
            if len(group) < 2:
                continue
            # merge postings into the div transaction
            try:
                div_tx = [e for e in group if "div" in e.meta][0]
            except IndexError:
                continue
            for e in group:
                if e != div_tx:
                    div_tx.postings.extend(e.postings)
                    entries.remove(e)

            # clean-up meta tags
            # del div_tx.meta["div_type"]
            # del div_tx.meta["div"]
            # del div_tx.meta["isin"]

            # merge postings with the same account
            grouped_postings = defaultdict(list)
            additional_postings = []
            for p in div_tx.postings:
                # don't group tax reversals
                if p.meta and p.meta.get("filename") == "tax_reversal":
                    additional_postings.append(p)
                else:
                    grouped_postings[p.account].append(p)
            div_tx.postings.clear()
            for account, postings in grouped_postings.items():
                div_tx.postings.append(
                    data.Posting(
                        account,
                        reduce(amount_add, (p.units for p in postings)),  # type: ignore
                        None,
                        None,
                        None,
                        None,
                    )
                )
            # add the additional postings
            div_tx.postings.extend(additional_postings)
        return entries

    def merge_forex(self, transactions):
        """
        Merge forex transactions for the same day and currency pair.
        """
        grouped = defaultdict(list)
        for txn in transactions:
            if not isinstance(txn, data.Transaction):
                continue
            if "filename" in txn.meta and txn.meta.get("filename") == "FX Transaction":
                # Group by date and payee (currency pair)
                grouped[(txn.date, txn.payee)].append(txn)
        for group in grouped.values():
            if len(group) < 2:
                continue
            # merge postings into one transaction
            try:
                # final_tx = [txn for txn in group if "div" in txn.meta][0]
                final_tx = group[0]
            except IndexError:
                continue
            # Remove other transactions.
            for txn in group:
                if txn != final_tx:
                    final_tx.postings.extend(txn.postings)
                    transactions.remove(txn)

            # merge postings with the same account
            grouped_postings = defaultdict(list)
            for p in final_tx.postings:
                grouped_postings[p.account].append(p)
            final_tx.postings.clear()

            for account, postings in grouped_postings.items():
                # Round the amounts to 2 decimal places.
                amount_: amount.Amount = reduce(amount_add, (p.units for p in postings)),  # type: ignore
                number = amount_[0].number.quantize(Decimal("0.0001")) # type: ignore
                number = number.normalize()
                amount_ = amount.Amount(number, amount_[0].currency) # type: ignore
                # Create posting.
                final_tx.postings.append(
                    data.Posting(
                        account,
                        amount_,
                        None,
                        None,
                        None,
                        None,
                    )
                )
            # There should be only two postings after grouping.
            assert len(final_tx.postings) == 2
            # Append the price information.
            # Find the posting with negative amount.
            p_with_price: data.Posting | None = None
            price_info: amount.Amount | None = None
            for p in final_tx.postings:
                if p.units.number < 0:
                    p_with_price = p
                else:
                    price_info = amount.Amount(p.units.number, p.units.currency)

            assert p_with_price is not None
            assert price_info is not None
            for i in range(len(final_tx.postings)):
                if final_tx.postings[i] == p_with_price:
                    number: Decimal = price_info.number / p_with_price.units.number # type: ignore
                    number = number.quantize(Decimal("0.00001"))
                    number = abs(number)
                    price = amount.Amount(
                        number,
                        price_info.currency,
                    )
                    final_tx.postings[i] = final_tx.postings[i]._replace(price=price)

        return transactions

    def merge_trades(self, transactions):
        """
        Merge trades for the same day, symbol, and price.
        """
        trade_transactions = []
        non_trade_transactions = []

        for txn in transactions:
            if isinstance(txn, data.Transaction) and txn.meta.get("filename", "") == "trade":
                trade_transactions.append(txn)
            else:
                non_trade_transactions.append(txn)

        grouped_trades = defaultdict(list)
        for txn in trade_transactions:
            stock_posting = None
            for p in txn.postings:
                stock_account_prefix = self.get_account_name(AccountTypes.STOCK, symbol="").rsplit(":", 1)[0]
                if p.account.startswith(stock_account_prefix) and p.units.currency in self.symbol_to_isin:
                    stock_posting = p
                    break
            
            if stock_posting:
                stock_symbol = stock_posting.units.currency
                trade_price_per_unit = None
                if stock_posting.cost and stock_posting.cost.number_per is not None:
                    trade_price_per_unit = stock_posting.cost.number_per
                elif stock_posting.price and stock_posting.price.number is not None:
                    trade_price_per_unit = stock_posting.price.number
                
                if trade_price_per_unit is not None:
                    group_key = (txn.date, stock_symbol, trade_price_per_unit)
                    grouped_trades[group_key].append(txn)
                else:
                    # If a trade transaction but no valid stock posting, treat as non-mergeable
                    non_trade_transactions.append(txn)
            else:
                # If not a trade transaction, or no stock posting found, treat as non-mergeable
                non_trade_transactions.append(txn)

        final_transactions = []
        for group_key, group_list in grouped_trades.items():
            if len(group_list) > 1:
                final_tx = group_list[0]
                for txn_to_merge in group_list[1:]:
                    final_tx.postings.extend(txn_to_merge.postings)
                
                consolidated_postings = defaultdict(list)
                for p in final_tx.postings:
                    consolidated_postings[p.account].append(p)

                final_tx.postings.clear()
                for account, postings_list in consolidated_postings.items():
                    total_amount = reduce(amount_add, (p.units for p in postings_list))
                    
                    price = postings_list[0].price if postings_list[0].price else None
                    cost = postings_list[0].cost if postings_list[0].cost else None
                    flag = postings_list[0].flag if postings_list[0].flag else None
                    meta = postings_list[0].meta if postings_list[0].meta else None

                    final_tx.postings.append(
                        data.Posting(
                            account,
                            total_amount,
                            cost,
                            price,
                            flag,
                            meta,
                        )
                    )
                final_transactions.append(final_tx)
            else:
                final_transactions.extend(group_list)
        
        final_transactions.extend(non_trade_transactions)

        return final_transactions

    def date(self, filepath: str) -> datetime.date | None:
        """Archival date of the file"""
        logger.debug(f"Getting date for {filepath}")

        # return super().date(filepath)
        statements = ibflex.parser.parse(open(filepath, "r", encoding="utf-8"))

        return statements.FlexStatements[0].whenGenerated

    def cash_balances(self, cr):
        """Account balance assertions"""
        transactions = []
        for row in cr:
            if row.currency == "BASE_SUMMARY":
                continue  # this is a summary balance that is not needed for beancount
            amount_ = amount.Amount(row.endingCash, row.currency)

            transactions.append(
                data.Balance(
                    data.new_metadata("balance", 0),
                    row.toDate + datetime.timedelta(days=1),
                    self.get_account_name(AccountTypes.CASH, currency=row.currency),
                    amount_,
                    None,
                    None,
                )
            )
        return transactions

    def stock_balances(self, rows, statement):
        """Stock balance assertions"""
        if not statement:
            raise LookupError("No statement passed for the date")
        assert isinstance(statement, Types.FlexStatement)

        txns = []
        # date = self.get_balance_assertion_date(cash_report)
        date = self.get_statement_last_date(statement)

        # Balance is as of the next day
        date = date + datetime.timedelta(days=1)

        for row in rows:
            # Get the symbol from Beancount by ISIN
            # row.symbol
            try:
                symbol = self.isin_to_symbol[row.isin]
            except KeyError as e:
                logger.error(f"Missing symbol entry for {row.isin}, {row.symbol}:")
                logger.warning(f"['', '{row.isin}'],")
                #raise e
                symbol = row.symbol

            acct_symbol = format_symbol_for_account_name(symbol)
            account = self.get_account_name(AccountTypes.STOCK, acct_symbol)
            # isin = row.isin

            txns.append(
                data.Balance(
                    data.new_metadata("balance", 0),
                    date,
                    account,
                    amount.Amount(row.position, symbol),
                    None,
                    None,
                )
            )

        return txns

    def fee_from_row(self, idx, row):
        """Converts fees to a beancount transaction"""
        amount_ = amount.Amount(row.amount, row.currency)
        text = row.description
        try:
            month = re.findall(r"\w{3} \d{4}", text)[0]
            narration = " ".join(["Fee", row.currency, month])
        except IndexError:
            narration = text

        # make the postings, two for fees
        postings = [
            # from
            data.Posting(
                # self.get_fees_account(row.currency), -amount_, None, None, None, None
                self.get_account_name(AccountTypes.FEES, row.symbol, row.currency),
                -amount_,
                None,
                None,
                None,
                None,
            ),
            # to
            data.Posting(
                self.get_account_name(AccountTypes.CASH, row.symbol, row.currency),
                amount_,
                None,
                None,
                None,
                None,
            ),
        ]

        # This can be made configurable.
        payee = "IB Commission Adjustment"
        meta = data.new_metadata(__file__, 0, {"descr": text})

        return data.Transaction(
            meta,
            row.reportDate,
            flags.FLAG_OKAY,
            payee,
            narration,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def interest_from_row(self, idx, row):
        amount_ = amount.Amount(row.amount, row.currency)
        # text = row.description
        # month = re.findall(r"\w{3}-\d{4}", text)[0]
        # narration = " ".join(["Interest ", row.currency, month])
        narration = row.description

        # make the postings, two for interest payments
        # received and paid interests are booked on the same account
        postings = [
            data.Posting(
                self.get_account_name(AccountTypes.CASH, currency=row.currency),
                amount_,
                None,
                None,
                None,
                None,
            ),
            data.Posting(
                self.get_account_name(AccountTypes.BRKINT, currency=row.currency),
                -amount_,
                None,
                None,
                None,
                None,
            ),
        ]
        meta = data.new_metadata("Interest", 0)
        return data.Transaction(
            meta,
            row.reportDate,
            flags.FLAG_OKAY,
            "Interactive Brokers",  # payee
            narration,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def trades(self, trades: Tuple[Types.Trade, ...]) -> list[data.Transaction]:
        # forex transactions
        fx = [
            t
            for t in trades
            if (not t.isin)
            and t.transactionType == TradeType.EXCHTRADE
            and is_forex_symbol(t.symbol)
        ]
        # Stocks transactions
        stocks = [t for t in trades if not is_forex_symbol(t.symbol)]

        return self.forex(fx) + self.stock_trades(stocks)

    def forex(self, fx):
        transactions = []
        for idx, row in enumerate(fx):
            symbol = row.symbol
            curr_prim, curr_sec = get_forex_currencies(symbol)
            currency_IBcommision = row.ibCommissionCurrency
            proceeds = amount.Amount(row.proceeds, curr_sec)
            quantity = amount.Amount(row.quantity, curr_prim)
            price = amount.Amount(row.tradePrice, curr_sec)
            commission = amount.Amount(row.ibCommission, currency_IBcommision)
            # buysell = row.buySell.name

            postings = [
                data.Posting(
                    # self.get_liquidity_account(curr_prim),
                    self.get_account_name(AccountTypes.CASH, symbol, curr_prim),
                    quantity,
                    None,
                    price,
                    None,
                    None,
                ),
                data.Posting(
                    # self.get_liquidity_account(curr_sec),
                    self.get_account_name(AccountTypes.CASH, symbol, curr_sec),
                    proceeds,
                    None,
                    None,
                    None,
                    None,
                ),
            ]

            # Add commission postings only if it is not zero
            if commission.number != 0:
                postings.append(
                    data.Posting(
                        # self.get_liquidity_account(currency_IBcommision),
                        self.get_account_name(
                            AccountTypes.CASH, symbol, currency_IBcommision
                        ),
                        commission,
                        None,
                        None,
                        None,
                        None,
                    )
                )

                try:
                    offset = minus(commission)
                except (ValueError, AssertionError):
                    logger.error(
                        f"Commission: {commission}, symbol: {symbol}, currency: {currency_IBcommision}"
                    )
                    offset = amount.Amount(Decimal(0), currency_IBcommision)
                postings.append(
                    data.Posting(
                        # self.get_fees_account(currency_IBcommision),
                        self.get_account_name(
                            AccountTypes.FEES, symbol, currency_IBcommision
                        ),
                        offset,
                        None,
                        None,
                        None,
                        None,
                    ),
                )

            # row.tradeDate
            txn_date = row.reportDate
            payee = f"FX {symbol}"

            transactions.append(
                data.Transaction(
                    data.new_metadata("FX Transaction", idx),
                    txn_date,
                    flags.FLAG_OKAY,
                    # payee
                    payee,
                    # " ".join([buysell, quantity.to_string(), "@", price.to_string()]),
                    None,
                    data.EMPTY_SET,
                    data.EMPTY_SET,
                    postings,
                )
            )
        return transactions

    def stock_trades(self, trades):
        """Generates transactions for IB stock trades.
        Tries to keep track of available holdings to disambiguate sales when lots are not enough,
        e.g. when there were multiple buys of the same symbol on the specific date.
        Currently, it does not take into account comission when calculating cost for stocks,
        just the trade price. It keeps the "real" cost as "ib_cost" metadata field though,
        which might be utilized in the future.
        It is mostly because I find the raw unafected price nicer to see in my beancount file.
        It also creates the fee posting for comission with "C" flag to distinguish it from other postings.
        """
        transactions = []

        for row, lots in iter_trades_with_lots(trades):
            if row.buySell in (BuySell.SELL, BuySell.CANCELSELL):
                op = "SELL"
            elif row.buySell in (BuySell.BUY, BuySell.CANCELBUY):
                op = "BUY"
            else:
                raise RuntimeError(f"Unknown buySell value: {row.buySell}")
            currency = row.currency
            assert isinstance(currency, str)

            currency_IBcommision = row.ibCommissionCurrency
            assert isinstance(currency_IBcommision, str)

            symbol = row.symbol
            assert isinstance(row.netCash, Decimal)
            net_cash = amount.Amount(row.netCash, currency)

            assert isinstance(row.ibCommission, Decimal)
            # commission = amount.Amount(row.ibCommission, currency_IBcommision)
            if row.taxes is not None:
                assert isinstance(row.taxes, Decimal)
                fees = amount.Amount(row.ibCommission + row.taxes, currency)
            else:
                fees = amount.Amount(row.ibCommission, currency_IBcommision)

            # Date
            # assert isinstance(row.tradeDate, datetime.date)
            assert isinstance(row.dateTime, datetime.date)
            date = row.dateTime.date()
            # Account. Use book symbol.
            if row.isin in self.isin_to_symbol:
                bc_symbol = self.isin_to_symbol[row.isin]
                account_symbol = format_symbol_for_account_name(bc_symbol)
            else:
                logger.warning(
                    f"Unknown symbol traded: {row.symbol} ({row.isin})"
                )
                bc_symbol = row.symbol or "UNKNOWN"
                account_symbol = format_symbol_for_account_name(bc_symbol)
            # amount
            assert isinstance(row.quantity, Decimal)
            # quantity = amount.Amount(row.quantity, get_currency_from_symbol(symbol))
            quantity = amount.Amount(row.quantity, bc_symbol)
            assert isinstance(row.tradePrice, Decimal)
            price = amount.Amount(row.tradePrice, currency)

            if row.openCloseIndicator == OpenClose.OPEN:
                # Purchase
                action = "Buy"
                self.add_holding(row)
                cost = position.CostSpec(
                    number_per=price.number,
                    number_total=None,
                    currency=currency,
                    date=row.tradeDate,
                    label=None,
                    merge=False,
                )
                lotpostings = [
                    data.Posting(
                        # self.get_asset_account(symbol),
                        self.get_account_name(
                            AccountTypes.STOCK, symbol=account_symbol
                        ),
                        quantity,
                        cost,
                        # price,
                        None,
                        None,
                        # {"ib_cost": row.cost},
                        None,
                    ),
                ]
            else:
                # Sale
                action = "Sell"
                lotpostings = []
                for clo in lots:
                    try:
                        clo_price = self.get_and_reduce_holding(clo)
                    except ValueError as e:
                        logger.warning(str(e))
                        clo_price = None

                    cost = position.CostSpec(
                        clo_price,
                        number_total=None,
                        currency=clo.currency,
                        date=clo.openDateTime.date(),
                        label=None,
                        merge=False,
                    )

                    lotpostings.append(
                        data.Posting(
                            # self.get_asset_account(symbol),
                            self.get_account_name(AccountTypes.STOCK, symbol=symbol),
                            amount.Amount(
                                -clo.quantity, get_currency_from_symbol(clo.symbol)
                            ),
                            cost,
                            price,
                            None,
                            # TODO: This is used to match the sale lot.
                            # {"ib_cost": clo.cost},
                            None,
                        )
                    )

                lotpostings.append(
                    data.Posting(
                        # self.get_pnl_account(symbol), None, None, None, None, None
                        self.get_account_name(AccountTypes.CAPGAIN, symbol=symbol),
                        None,
                        None,
                        None,
                        None,
                        None,
                    )
                )
            postings = (
                lotpostings
                + [
                    data.Posting(
                        # self.get_fees_account(currency_IBcommision),
                        self.get_account_name(
                            AccountTypes.FEES, currency=currency_IBcommision
                        ),
                        minus(fees),
                        None,
                        None,
                        # "C",
                        None,
                        None,
                    )
                ]
                + [
                    data.Posting(
                        self.get_account_name(AccountTypes.CASH, currency=currency),
                        net_cash,
                        None,
                        None,
                        None,
                        None,
                    )
                ]
            )

            payee = f"{action} {bc_symbol}"

            transactions.append(
                data.Transaction(
                    data.new_metadata("trade", 0),
                    date,
                    flags.FLAG_OKAY,
                    # symbol,  # payee
                    payee,
                    # " ".join([op, quantity.to_string(), "@", price.to_string()]),
                    None,
                    data.EMPTY_SET,
                    data.EMPTY_SET,
                    postings,
                )
            )

        return transactions

    def get_holdings_map(self, entries):
        root = realization.realize(entries)
        assets_account = self.get_account_name(AccountTypes.STOCK)
        account_parts = assets_account.split(":")
        for part in account_parts:
            if "{" in part:
                break
            if part not in root:
                return defaultdict(list)
            root = root[part]
        result = defaultdict(list)
        for account in realization.iter_children(root, leaf_only=True):
            for pos in account.balance:
                if pos.cost is None:
                    continue
                for tx in account.txn_postings:
                    real_price = None
                    if not isinstance(tx, data.TxnPosting):
                        continue
                    if (
                        tx.posting.units.currency == pos.units.currency
                        and tx.posting.cost.date == pos.cost.date
                        and tx.posting.cost.number == pos.cost.number
                        and "ib_cost" in tx.posting.meta
                    ):
                        real_price = abs(
                            tx.posting.meta["ib_cost"] / tx.posting.units.number
                        )
                    if real_price is None:
                        continue
                    self._adjust_holding(
                        result,
                        pos.cost.date,
                        pos.units.currency,
                        tx.posting.units.number,
                        tx.posting.cost.number,
                        real_price,
                    )
        return result

    def add_holding(self, row):
        holdings = self.holdings_map[
            (row.dateTime.date(), get_currency_from_symbol(row.symbol))
        ]
        for holding in holdings:
            if holding[2] == row.cost / row.quantity:
                holding[0] += row.quantity
                return
        holdings.append([row.quantity, row.tradePrice, row.cost / row.quantity])

    def get_and_reduce_holding(self, lot):
        holdings = self.holdings_map[
            (lot.openDateTime.date(), get_currency_from_symbol(lot.symbol))
        ]
        for i, holding in enumerate(holdings):
            quantity, price, real_price = holding
            if not (
                round(real_price, 4) == round(lot.cost / lot.quantity, 4)
                or (
                    quantity == lot.quantity
                    and round(real_price, 2) == round(lot.cost / lot.quantity, 2)
                )
            ):
                continue
            if (quantity < 0 and quantity > lot.quantity) or (
                quantity > 0 and quantity < lot.quantity
            ):
                raise ValueError(
                    f"not enough holdings of {lot.symbol} at {lot.openDateTime.date()}: have {quantity}, want {lot.quantity}"
                )
            if quantity == lot.quantity:
                holdings.pop(i)
            else:
                holding[0] -= lot.quantity
            return price
        raise ValueError(
            f"do not have {lot.symbol} {{ {lot.openDateTime.date()} }}: want {lot.quantity} at {lot.cost} ({lot.cost / lot.quantity} per unit). have {holdings}"
        )

    def _adjust_holding(self, holdings_map, date, symbol, quantity, price, real_price):
        lst = holdings_map[(date, symbol)]
        for i, (u, _, rp) in enumerate(lst):
            if round(rp, 4) == round(real_price, 4) or (
                u == quantity and round(rp, 2) == round(real_price, 2)
            ):
                lst[i][0] += quantity
                if lst[i][0] == 0:
                    lst.pop(i)
                return
        holdings_map[(date, symbol)].append([quantity, price, real_price])

    def get_balance_assertion_date(self, cash_report) -> datetime.date:
        """Get the date to use for balance assertions."""
        summary = cash_report[0]
        return summary.toDate

    def get_statement_last_date(self, statement) -> datetime.date:
        """Get the date to use for balance assertions."""
        return statement.toDate

    def corporate_actions(self, actions):
        transactions = []
        actions_map = defaultdict(list)
        for row in actions:
            actions_map[row.actionID].append(row)
        for action_group in actions_map.values():
            row = action_group[0]
            if row.type == Reorg.FORWARDSPLIT:
                assert len(action_group) == 1
                transactions.append(self.process_stock_forwardsplit(row))
            elif row.type == Reorg.MERGER:
                assert len(action_group) == 2
                transactions.append(self.process_stock_merger(action_group))
            elif row.type == Reorg.ISSUECHANGE:
                assert len(action_group) == 2
                transactions.append(self.process_issue_change(action_group))
            elif row.type == Reorg.RIGHTSISSUE:
                # Ignore?
                logger.warning(
                    f"ignoring rights issue: {row.dateTime}, {row.description}"
                )
            else:
                # Just log to the console.
                logger.warning(f"unknown corporate action type: {row.type} for {row.symbol}")
        return transactions

    def process_stock_forwardsplit(self, row):
        symbol = get_currency_from_symbol(row.symbol)
        m = re.search(r"SPLIT (\d+) FOR (\d+)", row.description)
        factor = Decimal(int(m.group(1)) / int(m.group(2)))
        holdings = [(k[0], v) for k, v in self.holdings_map.items() if k[1] == symbol]
        postings = []
        for date, lst in holdings:
            for quantity, price, real_price in lst:
                postings.append(
                    data.Posting(
                        # self.get_asset_account(row.symbol),
                        self.get_account_name(AccountTypes.STOCK, symbol=row.symbol),
                        amount.Amount(-quantity, symbol),
                        data.CostSpec(price, None, row.currency, date, None, False),
                        None,
                        None,
                        None,
                    )
                )
                postings.append(
                    data.Posting(
                        # self.get_asset_account(row.symbol),
                        self.get_account_name(AccountTypes.STOCK, symbol=row.symbol),
                        amount.Amount(quantity * factor, symbol),
                        data.CostSpec(
                            price / factor, None, row.currency, date, None, False
                        ),
                        None,
                        None,
                        {"ib_cost": round(real_price / factor * quantity, 6)},
                    )
                )
        for date, lst in holdings:
            for i in lst:
                i[0] *= Decimal(factor)
                i[1] /= Decimal(factor)
                i[2] /= Decimal(factor)
        return data.Transaction(
            data.new_metadata("corporateactions", 0),
            row.reportDate,
            flags.FLAG_OKAY,
            row.symbol,
            row.description,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def process_stock_merger(self, action_group):
        # This is almost certainly wrong for tax accounting
        row = action_group[0]
        symbol = get_currency_from_symbol(row.symbol)
        holdings = [(k[0], v) for k, v in self.holdings_map.items() if k[1] == symbol]
        postings = []
        for date, lst in holdings:
            for quantity, price, _real_price in lst:
                postings.append(
                    data.Posting(
                        # self.get_asset_account(row.symbol),
                        self.get_account_name(AccountTypes.STOCK, symbol=row.symbol),
                        amount.Amount(-quantity, symbol),
                        data.CostSpec(price, None, row.currency, date, None, False),
                        None,
                        None,
                        None,
                    )
                )
        for k in list(self.holdings_map.keys()):
            if k[1] == symbol:
                del self.holdings_map[k]
        postings.append(
            data.Posting(
                # self.get_liquidity_account(row.currency),
                self.get_account_name(AccountTypes.CASH, currency=row.currency),
                amount.Amount(row.proceeds, row.currency),
                None,
                None,
                None,
                None,
            )
        )
        postings.append(
            data.Posting(
                # self.get_pnl_account(symbol),
                self.get_account_name(AccountTypes.CAPGAIN, symbol=symbol),
                None,
                None,
                None,
                None,
                None,
            )
        )
        row = action_group[1]
        symbol = get_currency_from_symbol(row.symbol)
        postings.append(
            data.Posting(
                # self.get_asset_account(row.symbol),
                self.get_account_name(AccountTypes.STOCK, symbol=symbol),
                amount.Amount(row.quantity, get_currency_from_symbol(row.symbol)),
                data.CostSpec(
                    row.value / row.quantity,
                    None,
                    row.currency,
                    row.reportDate,
                    None,
                    None,
                ),
                None,
                None,
                None,
            )
        )
        self.holdings_map[(row.reportDate, symbol)].append(
            (row.quantity, row.value / row.quantity, row.value / row.quantity)
        )
        return data.Transaction(
            data.new_metadata("corporateactions", 0),
            row.reportDate,
            flags.FLAG_OKAY,
            row.symbol,
            row.description,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def process_issue_change(self, action_group):
        row = action_group[0]
        if row.symbol.endswith(".OLD"):
            row = action_group[1]
        old_symbol = re.search(r"(.*?)\(", row.description).group(1)
        holdings = [
            (k[0], v) for k, v in self.holdings_map.items() if k[1] == old_symbol
        ]
        postings = []
        for date, lst in holdings:
            for quantity, price, real_price in lst:
                postings.append(
                    data.Posting(
                        # self.get_asset_account(old_symbol),
                        self.get_account_name(AccountTypes.STOCK, symbol=old_symbol),
                        amount.Amount(-quantity, old_symbol),
                        data.CostSpec(price, None, row.currency, date, None, False),
                        None,
                        None,
                        None,
                    )
                )
                postings.append(
                    data.Posting(
                        # self.get_asset_account(row.symbol),
                        self.get_account_name(AccountTypes.STOCK, symbol=row.symbol),
                        amount.Amount(quantity, get_currency_from_symbol(row.symbol)),
                        data.CostSpec(price, None, row.currency, date, None, False),
                        None,
                        None,
                        {"ib_cost": quantity * real_price},
                    )
                )
            del self.holdings_map[(date, old_symbol)]
            self.holdings_map[(date, row.symbol)] = lst
        return data.Transaction(
            data.new_metadata("corporateactions", 0),
            row.reportDate,
            flags.FLAG_OKAY,
            row.symbol,
            row.description,
            data.EMPTY_SET,
            data.EMPTY_SET,
            postings,
        )

    def deduplicate(self, entries: data.Entries, existing: data.Entries) -> None:
        """Mark duplicates in extracted entries."""
        logger.debug(f"Deduplicating {len(entries)} entries against {len(existing)} existing entries")

        # return super().deduplicate(entries, existing)
        alens.importers.dedup.deduplicate(entries, existing)


_initial_missing = object()


def reduce(function, sequence, initial=_initial_missing):
    """
    reduce(function, iterable[, initial], /) -> value

    Apply a function of two arguments cumulatively to the items of an iterable, from left to right.

    This effectively reduces the iterable to a single value.  If initial is present,
    it is placed before the items of the iterable in the calculation, and serves as
    a default when the iterable is empty.

    For example, reduce(lambda x, y: x+y, [1, 2, 3, 4, 5])
    calculates ((((1 + 2) + 3) + 4) + 5).
    """

    it = iter(sequence)

    if initial is _initial_missing:
        try:
            value = next(it)
        except StopIteration:
            raise TypeError(
                "reduce() of empty iterable with no initial value"
            ) from None
    else:
        value = initial

    for element in it:
        value = function(value, element)

    return value


def format_decimal_for_beancount(number: Decimal) -> Decimal:
    """
    Format a decimal number to ensure at least 2 decimal places if it has any decimal places.
    
    Args:
        number: A Decimal number
        
    Returns:
        The formatted Decimal number with at least 2 decimal places if needed
    """
    # If the number has decimal places, ensure at least 2 decimal places
    decimal_places = get_number_of_decimal_places(number)
    if decimal_places > 0 and decimal_places < 2:
        return number.quantize(Decimal('0.00'))
    return number


def amount_add(a1: amount.Amount, a2: amount.Amount) -> amount.Amount:
    """
    add two amounts
    """
    if a1.currency == a2.currency:
        quant = a1.number + a2.number   # type: ignore
        
        # Ensure consistent decimal formatting
        # If either number has decimal places, ensure at least 2 decimal places in the result
        if '.' in str(a1.number) or '.' in str(a2.number):
            # Check how many decimal places each number has
            a1_decimals = get_number_of_decimal_places(a1.number)
            a2_decimals = get_number_of_decimal_places(a2.number)
            # Use at least 2 decimal places, or more if needed
            decimal_places = max(2, a1_decimals, a2_decimals)
            quant = quant.quantize(Decimal('0.' + '0' * decimal_places))
        
        return amount.Amount(quant, a1.currency)
    else:
        raise ValueError(
            f"Cannot add amounts of differnent currencies: {a1.currency} and {a2.currency}"
        )


def convert_date(self, d):
    """Converts a date string to a datetime object."""
    d = d.split(" ")[0]
    return datetime.datetime.strptime(d, self.date_format)


def get_currency_from_symbol(symbol):
    symbol = symbol.replace(" ", ".")
    if len(symbol) < 2:
        symbol = symbol + "STOCK"
    return symbol


def format_symbol_for_account_name(symbol: str) -> str:
    """Format a symbol for use in an account name."""
    if "." in symbol:
        symbol = symbol.replace(".", "-")
    if "_" in symbol:
        symbol = symbol.replace("_", "-")

    return symbol


def get_forex_currencies(symbol):
    b = re.search(r"(\w{3})[.](\w{3})", symbol)
    c = b.groups()
    return [c[0], c[1]]


def is_forex_symbol(symbol):
    """Determines if a transaction is a forex transaction based on the symbol.
    This, however, is wrong."""
    # returns True if a transaction is a forex transaction.
    b = re.search(r"(\w{3})[.](\w{3})", symbol)  # find something lile "USD.CHF"
    if b is None:  # no forex transaction, rather a normal stock transaction
        return False
    else:
        return True


def iter_trades_with_lots(trades):
    """Yields pairs of (trade, lots)."""
    it = iter(trades)
    trade = None
    lots = []
    while True:
        try:
            t = next(it)
        except StopIteration:
            break
        if isinstance(t, Types.Trade):
            if trade is not None:
                yield trade, lots
                lots = []
            trade = t
        elif isinstance(t, Types.Lot):
            lots.append(t)
        else:
            raise ValueError(f"Unknown trade element: {t}")
    if trade is not None:
        yield trade, lots


def minus(amt: amount.Amount) -> amount.Amount:
    """a minus operator"""
    # assert isinstance(amt.number, Decimal)
    assert amt.number is not None

    return amount.Amount(-amt.number, amt.currency)
