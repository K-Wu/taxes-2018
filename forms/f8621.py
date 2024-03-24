from . import utils
from typing import Any
import pandas


ACCOUNT_TO_ENGLISH_MAP = {
    "雪球": "XQ",
    "涨乐": "ZL",
    "支付宝": "ZFB",
    "国投瑞银": "GTRY",
    "中欧": "ZO",
    "雪球": "XQ",
    "理财通": "LCT",
    "且慢": "QM",
    "招商银行": "ZSYH",
}


def get_pfic_reference_name(row: pandas.Series) -> str:
    if row.isna()["基金编号"]:
        pfic_name = row["自定基金编号"]
    else:
        pfic_name = str(row["基金编号"])
    return ACCOUNT_TO_ENGLISH_MAP[row["账号"]] + "." + pfic_name


def fill_in_form(data_dict: dict[str, Any], output_path):
    utils.write_fillable_pdf("f8621.pdf", data_dict, "f8621.keys", output_path)
