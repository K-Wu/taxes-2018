if __name__ == "__main__":
    USD_TO_CNY = 7.104
    import json
    from qieman_parser.utils import (
        get_taxes_2018_root_path,
        convert_unix_millis_to_datetime,
        load_nav_by_ca,
        load_trade_records,
        produce_transaction_history,
        output_transaction_history,
    )
    import os

    for pfic_shorthand_name in ["snry", "zsjs"]:
        nav_records = load_nav_by_ca(
            "qieman_parser/tests/{}/nav_by_ca.txt".format(pfic_shorthand_name),
            2023,
        )
        trade_records = load_trade_records(
            "qieman_parser/tests/{}/dividend.txt".format(pfic_shorthand_name),
            "qieman_parser/tests/{}/trade_series.txt".format(
                pfic_shorthand_name
            ),
            2023,
        )
        df = produce_transaction_history(
            nav_records, trade_records, USD_TO_CNY
        )
        if not os.path.exists(
            os.path.join(
                get_taxes_2018_root_path(),
                "filled/2023/transactions",
            )
        ):
            os.makedirs(
                os.path.join(
                    get_taxes_2018_root_path(),
                    "filled/2023/transactions",
                )
            )
        output_transaction_history(
            df,
            os.path.join(
                get_taxes_2018_root_path(),
                "filled/2023/transactions/{}.csv".format(pfic_shorthand_name),
            ),
        )
