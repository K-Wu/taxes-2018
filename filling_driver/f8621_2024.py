import os
import pandas
from typing import Any
import forms.f8621
from qieman_parser.utils import load_shareholder_info, get_taxes_2018_root_path


def build_pfic_data_dict_for_2024(
    df: pandas.DataFrame,
    num_pfics: int,
    currency_suffix: str,
    usd_to_currency_exchange_rate: float,
) -> dict[str, dict[str, Any]]:
    """
    "基金英文" for name_foreign_corp_pfic_entity
    "Address" for  address_entity
    2024 for tax_year_entity
    "账号", "基金编号", "自定基金编号" for reference_id_number
    "Share class description" for description_class_shares
    "Date shares acquired" for date_shares_acquired_in_tax_year
    "2024年年底持有份额" for number_of_shares_held_at_end_year
    "2024年底总资产" for value_if_more_than_200k, value_150k_to_200k, value_100k_to_150k, value_50k_to_100k, value_0k_to_50k
    type_pfic_section_1296 is checked
    elect_to_mark_to_market_stock is checked
    "2024年MtM加总至ordinary income的收益" /currency_exchange_rates[2024] report positive in the box type_pfic_section_1296_excess_amount
    "2024年底总资产" /currency_exchange_rates[2024] for 10a_mark_to_market (fair market value)
    ("2024年底总资产" - "2024年收益")/currency_exchange_rates[2024] for 10b_mark_to_market (adjusted basis)
    "2024年收益"/currency_exchange_rates[2024] for 10c_mark_to_market
    0 for 11_mark_to_market, and 12_mark_to_market (unreversed inclusions)
    Keep Line 13--14 empty as they are related to sale or disposal
    """
    results_data_dict = {}
    shareholder_info = load_shareholder_info()
    for idx_row in range(0, num_pfics):  # len(df)):
        row = df.iloc[idx_row]
        pfic_name = forms.f8621.get_pfic_reference_name(row)
        assert (
            pfic_name not in results_data_dict
        ), "Duplicate PFIC name found in the data. Please check the data and try again."
        assert not row.isna()["2024年底持有份额"]
        number_of_shares_held_at_end_year = (row["2024年底持有份额"])

        # Break address into lines by inserting a new line character every 50 characters
        address_lines = [
            row["Address"][i : i + 50]
            for i in range(0, len(row["Address"]), 50)
        ]
        # If the end of the line is not space and the beginnng of the next line is not space, insert a hyphen
        for i in range(1, len(address_lines)):
            if address_lines[i - 1][-1] != " " and address_lines[i][0] != " ":
                address_lines[i - 1] += "-"
        # If the beginning of a line is a space, remove it
        for i in range(len(address_lines)):
            if address_lines[i][0] == " ":
                address_lines[i] = address_lines[i][1:]
        address = "\n".join(address_lines)

        results_data_dict[pfic_name] = {
            "name_shareholder": shareholder_info[0],
            "identifying_number": shareholder_info[1],
            "address": shareholder_info[2],
            "calendar_year": "24",
            "city_state_country": shareholder_info[3],
            "is_individual": True,
            "name_foreign_corp_pfic_entity": row["基金英文"],
            "address_entity": address,
            "tax_year_entity": "24",
            "reference_id_number": pfic_name,
            "description_class_shares": row["Share class description"],
            "date_shares_acquired_in_tax_year": row["购入时间（2024年税表）"],
            "number_of_shares_held_at_end_year": "{:.2f}".format(
                number_of_shares_held_at_end_year
            ),
            "type_pfic_section_1296": True,
            "elect_to_mark_to_market_stock": True,
        }
        if not type(row["购入时间（2024年税表）"]) == str:
            results_data_dict[pfic_name][
                "date_shares_acquired_in_tax_year"
            ] = row["购入时间（2024年税表）"].strftime("%Y-%m-%d")

        


        # If there is a sale, fill in Line 13--14 instaed of Line 10--12.
        # All sales in 2024 lead to sale of all shares.
        if number_of_shares_held_at_end_year == 0:
            fair_market_value = (row["2023年年底总资产" + currency_suffix] + row["清仓时相比2023年底收益" + currency_suffix]) / usd_to_currency_exchange_rate
            # Include 2023 gain in the adjusted basis. If there is a loss, the adjusted basis is the original basis.
            if row["2023年收益"+currency_suffix] <= 0:
                adjusted_basis = (row["2023年年底总资产" + currency_suffix] - row["2023年收益" + currency_suffix] ) / usd_to_currency_exchange_rate
            else:
                adjusted_basis = row["2023年年底总资产" + currency_suffix] / usd_to_currency_exchange_rate
            
            results_data_dict[pfic_name].update({ 
                "13a_mark_to_market": "{:.2f}".format( # fair market value
                    fair_market_value
                ),
                "13b_mark_to_market": "{:.2f}".format( # adjusted basis
                    adjusted_basis
                ),
                "13c_mark_to_market": "{:.2f}".format( # gain / loss before allowance
                    row["2024年收益" + currency_suffix] / usd_to_currency_exchange_rate
                ),
                "14a_mark_to_market": "0.", # unreversed inclusions
                "14b_mark_to_market": "0.", # allowed loss
            })
            results_data_dict[pfic_name]["13c_mark_to_market"] = "{:.2f}".format(float(results_data_dict[pfic_name]["13a_mark_to_market"]) - float(results_data_dict[pfic_name]["13b_mark_to_market"]))
            if row["2024年收益" + currency_suffix] / usd_to_currency_exchange_rate < 0:
                results_data_dict[pfic_name]["14c_mark_to_market"] = results_data_dict[pfic_name]["13c_mark_to_market"] # unallowed loss (capital loss)
            if row["2024年收益" + currency_suffix] / usd_to_currency_exchange_rate > 0:
                results_data_dict[pfic_name][
                    "type_pfic_section_1296_excess_amount"
                ] = results_data_dict[pfic_name]["13c_mark_to_market"]
        else:
            fair_market_value = row["2024年底总资产" + currency_suffix] / usd_to_currency_exchange_rate
            results_data_dict[pfic_name].update({ 
                "10a_mark_to_market": "{:.2f}".format( # fair market value
                    fair_market_value
                ),
                "10b_mark_to_market": "{:.2f}".format(row["2024年底adjusted basis" + currency_suffix] / usd_to_currency_exchange_rate), # adjusted basis
                "10c_mark_to_market": "{:.2f}".format( # gain / loss before allowance
                    row["2024年收益" + currency_suffix] / usd_to_currency_exchange_rate
                ),
                "11_mark_to_market": "0.", # unreversed inclusions
                "12_mark_to_market": "0.", # allowed loss
            })
            if (
                row["2024年MtM加总至ordinary income的收益" + currency_suffix]
                / usd_to_currency_exchange_rate
                > 0
            ):
                results_data_dict[pfic_name][
                    "type_pfic_section_1296_excess_amount"
                ] = "{:.2f}".format(
                    row["2024年MtM加总至ordinary income的收益" + currency_suffix]
                    / usd_to_currency_exchange_rate
                )

        
        # Fill in Line 4: Value of shares held at the end of the tax year
        if fair_market_value > 200000:
            print(pfic_name, ">200k", fair_market_value)
            results_data_dict[pfic_name]["value_if_more_than_200k"] = True
        elif fair_market_value > 150000:
            print(pfic_name, ">150k", fair_market_value)
            results_data_dict[pfic_name]["value_150k_to_200k"] = True
        elif fair_market_value > 100000:
            print(pfic_name, ">100k", fair_market_value)
            results_data_dict[pfic_name]["value_100k_to_150k"] = True
        elif fair_market_value > 50000:
            print(pfic_name, ">50k", fair_market_value)
            results_data_dict[pfic_name]["value_50k_to_100k"] = True
        else:
            results_data_dict[pfic_name]["value_0_to_50k"] = True
    return results_data_dict


if __name__ == "__main__":

    repo_root = get_taxes_2018_root_path()

    # Handle CNY mutual funds
    df = pandas.read_excel(
        "C:/Users/tonyw/OneDrive - MSFT/2025 Spring Tax Return/ForeignAccountDetails.xlsx",
        "人民币基金详情",
    )
    # excel_path = os.path.join("C:/Users/tonyw/OneDrive - KUNW-MSFT/2025 Spring Tax Return", "ForeignAccountDetails.xlsx")
    # exchange_rate_df = pandas.read_excel(excel_path, sheet_name="人民币基金详情")
    # usd_to_currency_exchange_rate = float(exchange_rate_df.iloc[0, excel_path.find("X75")])  # Read from cell X75
    usd_to_currency_exchange_rate = 7.104
    data_dict: dict[str, dict[str, Any]] = build_pfic_data_dict_for_2024(df, 66, "（人民币元）", usd_to_currency_exchange_rate)

    # Handle USD mutual funds
    df_usd = pandas.read_excel(
        "C:/Users/tonyw/OneDrive - MSFT/2025 Spring Tax Return/ForeignAccountDetails.xlsx",
        "美元基金详情",
    )
    data_usd_dict = build_pfic_data_dict_for_2024(df_usd, 1, "(USD)", 1.0)

    data_dict.update(data_usd_dict)
    
    if not os.path.exists(
        os.path.join(
            repo_root,
            "filled/2024/f8621",
        )
    ):
        os.makedirs(
            os.path.join(
                repo_root,
                "filled/2024/f8621",
            )
        )
    for pfic_reference_name in data_dict:
        forms.f8621.fill_in_form(
            data_dict[pfic_reference_name],
            os.path.join(
                repo_root,
                "filled/2024/f8621/",
                "{}.f8621.pdf".format(pfic_reference_name),
            ),
        )
