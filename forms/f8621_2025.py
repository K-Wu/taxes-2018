from . import utils
from typing import Any
import pandas


ACCOUNT_TO_ENGLISH_MAP = {
    "雪球": "XQ",
    "涨乐": "ZL",
    "支付宝": "ZFB",
    "国投瑞银": "GTRY",
    "中欧": "ZO",
    "理财通": "LCT",
    "且慢": "QM",
    "招商银行": "ZSYH",
}

# Keys that changed between the 2018 and 2025 revisions of Form 8621.
# The old form had a single combined 'city_state_country' field;
# the 2025 revision splits it into four separate fields.
OLD_KEY_TO_NEW_KEYS = {
    "city_state_country": [
        "city_or_town",
        "state_or_province",
        "country",
        "zip_or_postal_code",
    ],
}

# New fields added in the 2025 revision that have no old-form equivalent.
NEW_ONLY_KEYS = {"room_or_suite", "currency_code", "15e1_1291_fund", "15e2_1291_fund"}

# Old field that was removed (replaced by the split above).
REMOVED_KEYS = {"city_state_country"}

# The old 15e_1291_fund is replaced by 15e1_1291_fund and 15e2_1291_fund.
RENAMED_KEYS = {"15e_1291_fund": "15e2_1291_fund"}


def get_pfic_reference_name(row: pandas.Series) -> str:
    if row.isna()["基金编号"]:
        pfic_name = row["自定基金编号"]
    else:
        pfic_name = str(row["基金编号"])
    return ACCOUNT_TO_ENGLISH_MAP[row["账号"]] + "." + pfic_name


def migrate_data_dict(old_data_dict: dict[str, Any]) -> dict[str, Any]:
    """Translate a data_dict keyed for the old f8621.keys into one for f8621-2025.keys.

    Handles the address field split, 15e→15e1/15e2 rename, and passes
    through all keys that are unchanged between revisions.
    """
    new_dict: dict[str, Any] = {}
    for key, value in old_data_dict.items():
        if key.startswith("_"):
            new_dict[key] = value
            continue
        if key == "BUTTONS":
            new_dict[key] = value
            continue
        if key in REMOVED_KEYS:
            continue
        if key in RENAMED_KEYS:
            new_dict[RENAMED_KEYS[key]] = value
            continue
        new_dict[key] = value
    return new_dict


def fill_in_form(data_dict: dict[str, Any], output_path):
    utils.write_fillable_pdf(
        "f8621-2025.pdf", data_dict, "f8621-2025.keys", output_path
    )
