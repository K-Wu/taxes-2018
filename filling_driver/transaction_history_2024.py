if __name__ == "__main__":
    import pandas as pd
    import os
    from qieman_parser.utils import get_taxes_2018_root_path
    
    # Read the exchange rate from the Excel file
    excel_path = os.path.join("C:/Users/kunw/OneDrive - KUNW-MSFT/2025 Spring Tax Return", "ForeignAccountDetails.xlsx")
    exchange_rate_df = pd.read_excel(excel_path, sheet_name="人民币基金详情")
    USD_TO_CNY = float(exchange_rate_df.iloc[0, excel_path.find("X75")])  # Read from cell X75
    print(f"Using USD to CNY exchange rate: {USD_TO_CNY}")
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
            "C:/Users/kunw/OneDrive - KUNW-MSFT/2025 Spring Tax Return/qieman/{}-nav.json".format(pfic_shorthand_name),
            2024,
        )
        trade_records = load_trade_records(
            "C:/Users/kunw/OneDrive - KUNW-MSFT/2025 Spring Tax Return/qieman/{}-trade-series.json".format(
                pfic_shorthand_name
            ),
            2024,
        )
        df = produce_transaction_history(
            nav_records, trade_records, USD_TO_CNY
        )
        if not os.path.exists(
            os.path.join(
                get_taxes_2018_root_path(),
                "filled/2024/transactions",
            )
        ):
            os.makedirs(
                os.path.join(
                    get_taxes_2018_root_path(),
                    "filled/2024/transactions",
                )
            )
        output_transaction_history(
            df,
            os.path.join(
                get_taxes_2018_root_path(),
                "filled/2024/transactions/{}.csv".format(pfic_shorthand_name),
            ),
        )
