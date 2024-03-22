import os
import git
import datetime
import json
import pandas


def is_taxes_2018_root_path(path: str) -> bool:
    """Adapted from https://github.com/K-Wu/HET_nsight_utils/blob/e6d6396905ebefc040c55f07777b59a5b9fe65db/detect_pwd.py"""
    try:
        # Check if we can find title as HET in README.md
        # File not found error during cat cannot be catched. So we use os.path.exists to check first
        if not os.path.exists(os.path.join(path, "README")):
            return False
        # Read the content in utf8
        with open(os.path.join(path, "README"), "r", encoding="utf8") as f:
            res = f.read()
        if (
            "Copyright (C) 2019 pyTaxPrep" in res
            and "A set of Python scripts to fill in common tax forms and schedules."
            in res
        ):
            return True
        return False
    except OSError:
        return False


def get_git_root_path(path: str = os.getcwd()) -> str:
    """Get the root path of the git repository.
    Adapted from https://github.com/K-Wu/HET_nsight_utils/blob/e6d6396905ebefc040c55f07777b59a5b9fe65db/detect_pwd.py
    """
    git_repo = git.Repo(path, search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    return git_root


def get_taxes_2018_root_path() -> str:
    """Go to the root path of the git repository, and go to the parent directory until we find the root path with the specified repo_title
    Adapted from https://github.com/K-Wu/HET_nsight_utils/blob/e6d6396905ebefc040c55f07777b59a5b9fe65db/detect_pwd.py
    """
    path = get_git_root_path()
    max_depth = 10
    idx_depth = 0
    while not is_taxes_2018_root_path(path):
        if idx_depth > max_depth:
            raise ValueError(
                f"Cannot find the root path with the specified repo_title: {repo_title}"
            )
        path = os.path.dirname(path)
        idx_depth += 1
    return path


def convert_unix_millis_to_datetime(millis: int) -> datetime:
    # txnDay in trade_series is in milliseconds
    # profitDate in nav_by_ca is in seconds
    """Convert unix milliseconds to datetime"""
    return datetime.datetime.fromtimestamp(millis / 1000.0).strftime(
        "%Y-%m-%d"
    )


def load_shareholder_info() -> list[str]:
    """Returns name_shareholder, identify_number, address, city_state_country for f8621"""
    with open(
        "C:/Users/tonyw/Box/2024 Spring/TaxReturn/KunWuShareholderInfo.txt"
    ) as fd:
        lines = fd.readlines()
    lines = [line.strip() for line in lines]
    return lines


def load_nav_by_ca(filename: str, tax_year: int) -> dict[str, float]:
    nav_by_ca = json.load(
        open(
            os.path.join(
                get_taxes_2018_root_path(),
                filename,
            ),
            encoding="utf8",
        )
    )
    nav_records: dict[str, float] = {}
    for date_record in nav_by_ca["dataList"]:
        date_record: dict
        profitDate = date_record["profitDate"]
        # profitDate in nav_by_ca is in seconds
        date_record["canonicalizedProfitDate"] = (
            convert_unix_millis_to_datetime(profitDate * 1000)
        )

        # Skipping records that are not in tax_year
        if (
            int(date_record["canonicalizedProfitDate"].split("-")[0])
            != tax_year
        ):
            continue

        nav_records[date_record["canonicalizedProfitDate"]] = float(
            date_record["nav"]
        )
    return nav_records


def load_trade_records(
    dividend_filename: str, trade_series_filename: str, tax_year: int
) -> dict[str, dict[str, float]]:
    dividend = json.load(
        open(
            os.path.join(
                get_taxes_2018_root_path(),
                dividend_filename,
            ),
            encoding="utf8",
        )
    )
    trade_series = json.load(
        open(
            os.path.join(
                get_taxes_2018_root_path(),
                trade_series_filename,
            ),
            encoding="utf8",
        )
    )

    trade_records: dict[str, dict[str, float]] = {}
    for trade_record in trade_series["series"]:
        trade_record: dict
        txnDay = trade_record["txnDay"]
        # txnDay in trade_series is in milliseconds
        trade_record["canonicalizedTxnDate"] = convert_unix_millis_to_datetime(
            txnDay
        )

        # Skipping records that are not in tax_year
        if int(trade_record["canonicalizedTxnDate"].split("-")[0]) != tax_year:
            continue

        # Skipping rebalance
        if trade_record["rebalance"] != 0:
            assert trade_record["rebalance"] == 1
            continue
        trade_records[trade_record["canonicalizedTxnDate"]] = {
            # "rebalance": float(trade_record["rebalance"]),
            "dividend_reinvest": 0,
            "buy": float(trade_record["buy"]),
            "redeem": float(trade_record["redeem"]),
        }
    for date in dividend:
        if date not in trade_records:
            trade_records[date] = {"buy": 0, "redeem": 0}
        trade_records[date]["dividend_reinvest"] = float(dividend[date]["CNY"])
    return trade_records


def produce_transaction_history(
    trade_records, nav_records, usd_to_cny: float
) -> pandas.DataFrame:
    """Produce a transaction history dataframe"""
    df = pandas.DataFrame(
        {
            "Date": [],
            "Transaction type": [],
            "Amount (CNY)": [],
            "NAV (CNY)": [],
            "Amount (USD)": [],
            "NAV (USD)": [],
        }
    )
    nav_map = {date: nav for date, nav in nav_records.items()}
    for date, trade_record in trade_records.items():
        if date not in nav_map:
            raise ValueError(f"Date {date} not found in nav_map")
        nav = nav_map[date]
        if trade_record["buy"] > 0:
            df = df.append(
                {
                    "Date": date,
                    "Transaction type": "Buy",
                    "Amount (CNY)": trade_record["buy"],
                    "NAV (CNY)": nav,
                    "Amount (USD)": trade_record["buy"] / usd_to_cny,
                    "NAV (USD)": nav / usd_to_cny,
                },
                ignore_index=True,
            )
        if trade_record["redeem"] > 0:
            df = df.append(
                {
                    "Date": date,
                    "Transaction type": "Redeem",
                    "Amount (CNY)": trade_record["redeem"],
                    "NAV (CNY)": nav,
                    "Amount (USD)": trade_record["redeem"] / usd_to_cny,
                    "NAV (USD)": nav / usd_to_cny,
                },
                ignore_index=True,
            )
        if trade_record["dividend_reinvest"] > 0:
            df = df.append(
                {
                    "Date": date,
                    "Transaction type": "Dividend reinvest",
                    "Amount (CNY)": trade_record["dividend_reinvest"],
                    "NAV (CNY)": nav,
                    "Amount (USD)": trade_record["dividend_reinvest"]
                    / usd_to_cny,
                },
                ignore_index=True,
            )
    return df

def output_transaction_history(df: pandas.DataFrame, output_filename: str):
    """Output transaction history dataframe to a file"""
    df.to_csv(output_filename, index=False)
