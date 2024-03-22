if __name__ == "__main__":
    import json
    from ..utils import get_taxes_2018_root_path
    import os
    json.load(open(os.path.join(get_taxes_2018_root_path(), "qieman_parser/tests/snry/dividend.txt"),encoding='utf8'))