import os
import pandas
from typing import Any
import forms.f8621
from qieman_parser.utils import load_shareholder_info, get_taxes_2018_root_path


def build_pfic_data_dict_for_2023(
    df: pandas.DataFrame,
) -> dict[str, dict[str, Any]]:
    """
    "基金英文" for name_foreign_corp_pfic_entity
    "Address" for  address_entity
    2023 for tax_year_entity
    "账号", "基金编号", "自定基金编号" for reference_id_number
    "Share class description" for description_class_shares
    "Date shares acquired" for date_shares_acquired_in_tax_year
    "2023年年底持有份额（货币基金，雪球组合和支付宝锐意进取1元==1份）" for number_of_shares_held_at_end_year
    If previous is not available, use "2023年年底总资产（人民币元）"/ "2023年年底每股价格（人民币元，如果持有份额无法直接获取，请填写）" for number_of_shares_held_at_end_year
    "2023年年底总资产（人民币元）" for value_if_more_than_200k, value_150k_to_200k, value_100k_to_150k, value_50k_to_100k, value_0k_to_50k
    type_pfic_section_1296 is checked
    elect_to_mark_to_market_stock is checked
    "2023年MtM加总至ordinary income的收益（人民币元）"/currency_exchange_rates[2023] report positive in the box type_pfic_section_1296_excess_amount
    "2023年年底总资产（人民币元）"/currency_exchange_rates[2023] for 10a_mark_to_market (fair market value)
    ("2023年年底总资产（人民币元）" - "2023年收益（人民币元）")/currency_exchange_rates[2023] for 10b_mark_to_market (adjusted basis)
    "2023年收益（人民币元）"/currency_exchange_rates[2023] for 10c_mark_to_market
    0 for 11_mark_to_market, and 12_mark_to_market (unreversed inclusions)
    Keep Line 13--14 empty as they are related to sale or disposal
    """
    USD_TO_CNY_2023 = 7.104
    NUM_PFICS = 66
    results_data_dict = {}
    shareholder_info = load_shareholder_info()
    for idx_row in range(0, NUM_PFICS):  # len(df)):
        row = df.iloc[idx_row]
        pfic_name = forms.f8621.get_pfic_reference_name(row)
        assert (
            pfic_name not in results_data_dict
        ), "Duplicate PFIC name found in the data. Please check the data and try again."
        if row.isna()[
            "2023年年底持有份额（货币基金，雪球组合和支付宝锐意进取1元==1份）"
        ]:
            number_of_shares_held_at_end_year = (
                row["2023年年底总资产（人民币元）"]
                / row[
                    "2023年年底每股价格（人民币元，如果持有份额无法直接获取，请填写）"
                ]
            )
        else:
            number_of_shares_held_at_end_year = row[
                "2023年年底持有份额（货币基金，雪球组合和支付宝锐意进取1元==1份）"
            ]

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
            "identify_number": shareholder_info[1],
            "address": shareholder_info[2],
            "city_state_country": shareholder_info[3],
            "is_individual": True,
            "name_foreign_corp_pfic_entity": row["基金英文"],
            "address_entity": address,
            "tax_year_entity": "23",
            "reference_id_number": pfic_name,
            "description_class_shares": row["Share class description"],
            "date_shares_acquired_in_tax_year": row["Date shares acquired"],
            "number_of_shares_held_at_end_year": "{:.2f}".format(
                number_of_shares_held_at_end_year
            ),
            "type_pfic_section_1296": True,
            "elect_to_mark_to_market_stock": True,
            "10a_mark_to_market": "{:.2f}".format(
                row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023
            ),
            "10b_mark_to_market": "{:.2f}".format(
                (
                    row["2023年年底总资产（人民币元）"]
                    - row["2023年收益（人民币元）"]
                )
                / USD_TO_CNY_2023
            ),
            "10c_mark_to_market": "{:.2f}".format(
                row["2023年收益（人民币元）"] / USD_TO_CNY_2023
            ),
            "11_mark_to_market": "0.",
            "12_mark_to_market": "0.",
        }
        if not type(row["Date shares acquired"]) == str:
            results_data_dict[pfic_name][
                "date_shares_acquired_in_tax_year"
            ] = row["Date shares acquired"].strftime("%Y-%m-%d")
        if (
            row["2023年MtM加总至ordinary income的收益（人民币元）"]
            / USD_TO_CNY_2023
            > 0
        ):
            results_data_dict[pfic_name][
                "type_pfic_section_1296_excess_amount"
            ] = "{:.2f}".format(
                row["2023年MtM加总至ordinary income的收益（人民币元）"]
                / USD_TO_CNY_2023
            )
            assert (
                results_data_dict[pfic_name][
                    "type_pfic_section_1296_excess_amount"
                ]
                == results_data_dict[pfic_name]["10c_mark_to_market"]
            ), "The value for type_pfic_section_1296_excess_amount is not correct. Please check the data and try again."
        if row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023 > 200000:
            results_data_dict[pfic_name]["value_if_more_than_200k"] = (
                row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023
            )
        elif row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023 > 150000:
            results_data_dict[pfic_name]["value_150k_to_200k"] = True
        elif row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023 > 100000:
            results_data_dict[pfic_name]["value_100k_to_150k"] = True
        elif row["2023年年底总资产（人民币元）"] / USD_TO_CNY_2023 > 50000:
            results_data_dict[pfic_name]["value_50k_to_100k"] = True
        else:
            results_data_dict[pfic_name]["value_0_to_50k"] = True
    return results_data_dict


if __name__ == "__main__":

    repo_root = get_taxes_2018_root_path()
    df = pandas.read_excel(
        "C:/Users/tonyw/Box/2024 Spring/TaxReturn/CapitalLoss.xlsx",
        "基金详情",
    )
    data_dict: dict[str, dict[str, Any]] = build_pfic_data_dict_for_2023(df)
    if not os.path.exists(
        os.path.join(
            repo_root,
            "filled/2023/f8621",
        )
    ):
        os.makedirs(
            os.path.join(
                repo_root,
                "filled/2023/f8621",
            )
        )
    for pfic_reference_name in data_dict:
        forms.f8621.fill_in_form(
            data_dict[pfic_reference_name],
            os.path.join(
                repo_root,
                "filled/2023/f8621/",
                "{}.f8621.pdf".format(pfic_reference_name),
            ),
        )
