import os
import pandas
from typing import Any
import forms.f8621_2025
from qieman_parser.utils import get_taxes_2018_root_path

EXCEL_PATH = r"C:\Users\kunw\OneDrive - KUNW-MSFT\2025Tax\ForeignAccountDetails.xlsx"
SHAREHOLDER_INFO_PATH = r"C:\Users\kunw\OneDrive - KUNW-MSFT\2025 Spring Tax Return\KunWuShareholderInfo.txt"


def read_usd_to_cny_rate() -> float:
    """Read the USD/CNY exchange rate from cell AL75 in 人民币基金详情."""
    df = pandas.read_excel(EXCEL_PATH, sheet_name="人民币基金详情", header=None, nrows=75)
    return float(df.iloc[74, 37])  # AL75: row 75 (0-indexed 74), col AL (index 37)


def load_shareholder_info_2025() -> dict[str, str]:
    """Parse KunWuShareholderInfo.txt into the split address fields required
    by the 2025 revision of Form 8621.

    File format (4 lines):
        Kun Wu
        686-31-9209
        2530 Zanker Rd SCR-01-6120
        San Jose, CA 95131
    """
    with open(SHAREHOLDER_INFO_PATH) as fd:
        lines = [line.strip() for line in fd.readlines()]

    city_state_zip = lines[3]
    city, state_zip = city_state_zip.rsplit(",", 1)
    state_zip = state_zip.strip()
    parts = state_zip.split()
    state = parts[0]
    zip_code = parts[1] if len(parts) > 1 else ""

    return {
        "name_shareholder": lines[0],
        "identifying_number": lines[1],
        "address": lines[2],
        "city_or_town": city,
        "state_or_province": state,
        "country": "US",
        "zip_or_postal_code": zip_code,
    }


def format_address_entity(raw_address: str) -> str:
    """Break long PFIC entity addresses into multiple lines."""
    address_lines = [raw_address[i : i + 50] for i in range(0, len(raw_address), 50)]
    for i in range(1, len(address_lines)):
        if address_lines[i - 1][-1] != " " and address_lines[i][0] != " ":
            address_lines[i - 1] += "-"
    for i in range(len(address_lines)):
        if address_lines[i][0] == " ":
            address_lines[i] = address_lines[i][1:]
    return "\n".join(address_lines)


def build_base_data_dict(
    row: pandas.Series,
    shareholder: dict[str, str],
) -> dict[str, Any]:
    """Build the common portion of a data_dict shared by all PFIC types."""
    return {
        **shareholder,
        "calendar_year": "25",
        "is_individual": True,
        "name_foreign_corp_pfic_entity": row["基金英文"],
        "address_entity": format_address_entity(row["Address"]),
        "tax_year_entity": "25",
        "reference_id_number": forms.f8621_2025.get_pfic_reference_name(row),
        "description_class_shares": row["Share class description"],
        "type_pfic_section_1296": True,
        "elect_to_mark_to_market_stock": True,
    }


def set_value_bracket(d: dict[str, Any], fair_market_value_usd: float):
    """Fill Line 4 value-of-shares checkbox based on USD fair market value."""
    if fair_market_value_usd > 200000:
        d["value_if_more_than_200k"] = "{:.2f}".format(fair_market_value_usd)
    elif fair_market_value_usd > 150000:
        d["value_150k_to_200k"] = True
    elif fair_market_value_usd > 100000:
        d["value_100k_to_150k"] = True
    elif fair_market_value_usd > 50000:
        d["value_50k_to_100k"] = True
    else:
        d["value_0_to_50k"] = True


def build_cny_pfic_data_dicts(
    df: pandas.DataFrame,
    usd_to_cny: float,
) -> dict[str, dict[str, Any]]:
    shareholder = load_shareholder_info_2025()
    results: dict[str, dict[str, Any]] = {}

    for idx_row in range(len(df)):
        row = df.iloc[idx_row]
        shares_raw = row["2025年底持有份额"]
        shares = pandas.to_numeric(shares_raw, errors="coerce")
        is_sold_2025 = pandas.notna(row["清仓日.1"])
        is_held_2025 = pandas.notna(shares) and shares > 0

        if not is_sold_2025 and not is_held_2025:
            continue

        pfic_name = forms.f8621_2025.get_pfic_reference_name(row)
        assert pfic_name not in results, f"Duplicate PFIC: {pfic_name}"

        d = build_base_data_dict(row, shareholder)

        date_acquired = row["购入时间（2025年税表）"]
        if not isinstance(date_acquired, str) and pandas.notna(date_acquired):
            date_acquired = date_acquired.strftime("%Y-%m-%d")
        d["date_shares_acquired_in_tax_year"] = date_acquired

        if is_sold_2025 and not is_held_2025:
            # ---------- Completely sold in 2025 → Line 13-14 ----------
            d["number_of_shares_held_at_end_year"] = "0"

            fmv_cny = row["2024年底总资产（人民币元）"] + row["清仓时相比2024年底收益（人民币元）"]
            if row["2024年收益（人民币元）"] <= 0:
                basis_cny = row["2024年底总资产（人民币元）"] - row["2024年收益（人民币元）"]
            else:
                basis_cny = row["2024年底总资产（人民币元）"]

            fmv_usd = fmv_cny / usd_to_cny
            basis_usd = basis_cny / usd_to_cny
            gain_usd = fmv_usd - basis_usd

            d["13a_mark_to_market"] = "{:.2f}".format(fmv_usd)
            d["13b_mark_to_market"] = "{:.2f}".format(basis_usd)
            d["13c_mark_to_market"] = "{:.2f}".format(gain_usd)
            d["14a_mark_to_market"] = "0."
            d["14b_mark_to_market"] = "0."
            if gain_usd < 0:
                d["14c_mark_to_market"] = d["13c_mark_to_market"]
            if gain_usd > 0:
                d["type_pfic_section_1296_excess_amount"] = d["13c_mark_to_market"]

            set_value_bracket(d, fmv_usd)

        else:
            # ---------- Still held at year-end → Line 10-12 ----------
            d["number_of_shares_held_at_end_year"] = "{:.2f}".format(shares)

            fmv_usd = row["2025年底总资产（人民币元）"] / usd_to_cny
            basis_usd = row["2025年底adjusted basis（人民币元）"] / usd_to_cny
            gain_usd = row["2025年收益（人民币元）"] / usd_to_cny

            d["10a_mark_to_market"] = "{:.2f}".format(fmv_usd)
            d["10b_mark_to_market"] = "{:.2f}".format(basis_usd)
            d["10c_mark_to_market"] = "{:.2f}".format(gain_usd)
            d["11_mark_to_market"] = "0."
            d["12_mark_to_market"] = "0."

            mtm_income_cny = pandas.to_numeric(
                row["2025年MtM加总至ordinary income的收益（人民币元）"], errors="coerce"
            )
            if pandas.notna(mtm_income_cny) and mtm_income_cny > 0:
                d["type_pfic_section_1296_excess_amount"] = "{:.2f}".format(
                    mtm_income_cny / usd_to_cny
                )

            set_value_bracket(d, fmv_usd)

        results[pfic_name] = d

    return results


def build_usd_pfic_data_dicts(
    df: pandas.DataFrame,
) -> dict[str, dict[str, Any]]:
    shareholder = load_shareholder_info_2025()
    results: dict[str, dict[str, Any]] = {}

    for idx_row in range(len(df)):
        row = df.iloc[idx_row]
        if pandas.isna(row["2025年清仓adjusted basis(USD)"]):
            continue

        pfic_name = forms.f8621_2025.get_pfic_reference_name(row)
        assert pfic_name not in results, f"Duplicate PFIC: {pfic_name}"

        d = build_base_data_dict(row, shareholder)

        date_acquired = row["购入时间（2025年）"]
        if not isinstance(date_acquired, str) and pandas.notna(date_acquired):
            date_acquired = date_acquired.strftime("%Y-%m-%d")
        d["date_shares_acquired_in_tax_year"] = str(date_acquired) if pandas.notna(date_acquired) else "Not applicable"

        d["number_of_shares_held_at_end_year"] = "0"

        fmv_usd = float(row["2025年底清仓总资产(USD)"])
        basis_usd = float(row["2025年清仓adjusted basis(USD)"])
        gain_usd = fmv_usd - basis_usd

        d["13a_mark_to_market"] = "{:.2f}".format(fmv_usd)
        d["13b_mark_to_market"] = "{:.2f}".format(basis_usd)
        d["13c_mark_to_market"] = "{:.2f}".format(gain_usd)
        d["14a_mark_to_market"] = "0."
        d["14b_mark_to_market"] = "0."
        if gain_usd < 0:
            d["14c_mark_to_market"] = d["13c_mark_to_market"]
        if gain_usd > 0:
            d["type_pfic_section_1296_excess_amount"] = d["13c_mark_to_market"]

        set_value_bracket(d, fmv_usd)
        results[pfic_name] = d

    return results


if __name__ == "__main__":
    repo_root = get_taxes_2018_root_path()
    output_dir = os.path.join(repo_root, "filled", "2025", "f8621")
    os.makedirs(output_dir, exist_ok=True)

    usd_to_cny = read_usd_to_cny_rate()
    print(f"Using USD/CNY exchange rate: {usd_to_cny}")

    df_cny = pandas.read_excel(EXCEL_PATH, sheet_name="人民币基金详情")
    data_dict = build_cny_pfic_data_dicts(df_cny, usd_to_cny)
    print(f"CNY PFICs: {len(data_dict)} forms to generate")

    df_usd = pandas.read_excel(EXCEL_PATH, sheet_name="美元基金详情")
    data_usd = build_usd_pfic_data_dicts(df_usd)
    print(f"USD PFICs: {len(data_usd)} forms to generate")

    data_dict.update(data_usd)

    for pfic_name, pfic_data in data_dict.items():
        output_path = os.path.join(output_dir, f"{pfic_name}.f8621.pdf")
        forms.f8621_2025.fill_in_form(pfic_data, output_path)
    print(f"Generated {len(data_dict)} f8621 forms in {output_dir}")
