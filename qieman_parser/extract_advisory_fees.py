"""
从且慢投顾费HTML页面中提取各基金的月度投顾服务费，输出为CSV文件。
"""

import re
import csv
import sys

INPUT_FILE = r'c:\Users\tonyw\OneDrive - MSFT\2025Tax\且慢投顾费.html'
OUTPUT_FILE = r'c:\Users\tonyw\OneDrive - MSFT\2025Tax\且慢投顾费.csv'


def extract_fees(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern: month header followed by multiple fund entries
    # Month header: <p class="fy9bu0-4 ksuRoR">2025年12月</p>
    # Fund name:    <p class="sc-1il4bz9-4 bXmVdn">基金名</p>
    # Amount:       <span class="number__d152d">5.34<span class="unit__ae3db">元</span></span>

    # Split by month sections
    month_pattern = r'class="fy9bu0-4 ksuRoR">(2025年\d{1,2}月)</p>'
    month_splits = re.split(month_pattern, content)

    # month_splits: [before_first_month, month1, section1, month2, section2, ...]
    records = []  # list of (month, fund_name, amount)

    for i in range(1, len(month_splits), 2):
        month = month_splits[i]
        section = month_splits[i + 1]

        # Find all fund+fee pairs in this section
        # Each entry: fund name followed by 投顾服务费收取 and amount
        entry_pattern = (
            r'class="sc-1il4bz9-4 bXmVdn">(.*?)</p>'
            r'.*?投顾服务费收取.*?'
            r'class="number__d152d">([\d.]+)<span'
        )
        entries = re.findall(entry_pattern, section)
        for fund_name, amount in entries:
            records.append((month, fund_name, float(amount)))

    return records


def month_sort_key(month_str):
    """Sort key for '2025年X月' format."""
    m = re.match(r'(\d+)年(\d+)月', month_str)
    return (int(m.group(1)), int(m.group(2)))


def write_csv(records, output_path):
    # Collect all fund names and months
    funds = sorted(set(r[1] for r in records))
    months = sorted(set(r[0] for r in records), key=month_sort_key)

    # Build lookup: (month, fund) -> amount
    lookup = {}
    for month, fund, amount in records:
        # If same month+fund appears multiple times, sum them
        key = (month, fund)
        lookup[key] = lookup.get(key, 0) + amount

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['月份'] + funds)
        for month in months:
            row = [month]
            for fund in funds:
                val = lookup.get((month, fund), 0)
                row.append(f'{val:.2f}' if val else '')
            writer.writerow(row)

    # Print summary
    print(f'提取到 {len(records)} 条记录')
    print(f'基金: {", ".join(funds)}')
    print(f'月份: {len(months)} 个')
    print(f'已写入: {output_path}')

    # Print the table for verification
    print()
    header = f'{"月份":<12}' + ''.join(f'{f:>16}' for f in funds)
    print(header)
    print('-' * len(header))
    total = {f: 0.0 for f in funds}
    for month in months:
        line = f'{month:<12}'
        for fund in funds:
            val = lookup.get((month, fund), 0)
            total[fund] += val
            line += f'{val:>16.2f}' if val else f'{"":>16}'
        print(line)
    print('-' * len(header))
    line = f'{"合计":<12}'
    for fund in funds:
        line += f'{total[fund]:>16.2f}'
    print(line)


if __name__ == '__main__':
    records = extract_fees(INPUT_FILE)
    write_csv(records, OUTPUT_FILE)
