import calendar
import re
from datetime import datetime
from datetime import timedelta

import pendulum


def format_time(time):
    """将秒格式化为 xx时xx分格式"""
    result = ""
    hour = time // 3600
    if hour > 0:
        result += f"{hour}时"
    minutes = time % 3600 // 60
    if minutes > 0:
        result += f"{minutes}分"
    return result


def format_date(date, format="%Y-%m-%d %H:%M:%S"):
    return date.strftime(format)


def timestamp_to_date(timestamp):
    """时间戳转化为date"""
    return datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)


def get_first_and_last_day_of_month(date):
    # 获取给定日期所在月的第一天
    first_day = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在月的最后一天
    _, last_day_of_month = calendar.monthrange(date.year, date.month)
    last_day = date.replace(
        day=last_day_of_month, hour=0, minute=0, second=0, microsecond=0
    )

    return first_day, last_day


def get_first_and_last_day_of_year(date):
    # 获取给定日期所在年的第一天
    first_day = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在年的最后一天
    last_day = date.replace(month=12, day=31, hour=0, minute=0, second=0, microsecond=0)

    return first_day, last_day


def get_first_and_last_day_of_week(date):
    # 获取给定日期所在周的第一天（星期一）
    first_day_of_week = (date - timedelta(days=date.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 获取给定日期所在周的最后一天（星期日）
    last_day_of_week = first_day_of_week + timedelta(days=6)

    return first_day_of_week, last_day_of_week


def str_to_timestamp(date):
    if date == None:
        return 0
    dt = pendulum.parse(date)
    # 获取时间戳
    return int(dt.timestamp())


def truncate_string(s, length=30):
    """
    智能截取字符串作为标题
    规则：
    1. 跳过开头的 URL（https://...）
    2. 过滤掉标签（#xxx）
    3. 过滤掉 Markdown 格式符号（**、__、*、_等）
    4. 设置最小长度（至少 15 字符）
    5. 在标点符号处截断（更自然）
    6. 最多 30 字符
    """
    # 跳过开头的 URL
    s = re.sub(r'^https?://\S+\s*', '', s.strip())

    # 跳过"关联自"或"关联到"开头（多种冒号格式）
    s = re.sub(r'^关联[自到][：:]\s*', '', s)

    # 过滤掉标签（#开头的词）
    s = re.sub(r'#\S+\s*', '', s)

    # 过滤掉 Markdown 格式符号
    s = re.sub(r'\*\*|__|\*|_(?=\w)', '', s)  # 移除 **、__、*、_

    # 清理多余的空格
    s = ' '.join(s.split())

    # 如果处理后为空，返回默认标题
    if not s:
        return "无标题"

    # 如果总长度小于等于 length，直接返回
    if len(s) <= length:
        return s

    # 设置最小长度（至少 15 字符）
    min_length = min(15, length)

    # 正则表达式匹配标点符号或换行符
    pattern = re.compile(r'[，。！？；：,.!?;:\n]')

    # 查找所有匹配的位置
    matches = list(pattern.finditer(s))

    if not matches:
        # 如果没有找到标点符号，直接截取到 length
        return s[:length]

    # 寻找第一个 >= min_length 且 <= length 的标点符号
    end_pos = length
    for match in matches:
        pos = match.start()
        if min_length <= pos <= length:
            end_pos = pos
            break
        elif pos > length:
            # 如果所有标点都在 length 之后，使用前一个标点
            if matches and matches[0].start() >= min_length:
                end_pos = matches[0].start()
            break

    result = s[:end_pos].strip()

    # 如果最终结果为空或太短，返回默认截取
    if len(result) < min_length:
        return s[:length]

    return result


def is_within_n_days(target_date_str, n):
    # 将目标日期字符串转换为 datetime 对象
    target_date = datetime.strptime(target_date_str, '%Y-%m-%d %H:%M:%S')

    # 获取当前时间
    now = datetime.now()

    # 计算 n 天前的时间
    n_days_ago = now - timedelta(days=n)

    # 判断目标日期是否在 n 天内
    return n_days_ago <= target_date <= now