import os
import git
import datetime


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


def load_shareholder_info():
    """Returns name_shareholder, identify_number, address, city_state_country for f8621"""
    with open(
        "C:/Users/tonyw/Box/2024 Spring/TaxReturn/KunWuShareholderInfo.txt"
    ) as fd:
        lines = fd.readlines()
    lines = [line.strip() for line in lines]
    return lines
