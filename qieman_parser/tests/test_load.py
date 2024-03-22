if __name__ == "__main__":
    import json
    from ..utils import (
        get_taxes_2018_root_path,
        convert_unix_millis_to_datetime,
        load_nav_by_ca,
        load_trade_records,
    )
    import os

    nav_records = load_nav_by_ca(
        "qieman_parser/tests/snry/nav_by_ca.txt", 2023
    )
    trade_records = load_trade_records(
        "qieman_parser/tests/snry/dividend.txt",
        "qieman_parser/tests/snry/trade_series.txt",
        2023,
    )
