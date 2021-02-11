def get_nutrient_color(value):
    return 'text-success' if value <= 0.15 else 'text-danger'


def get_rank_suffix(i):
    i = i + 1
    if i >= 11 and 11 <= int(str(i)[-2:]) <= 13:
        return f'{i}th'
    remainder = i % 10
    if remainder == 1:
        return f'{i}st'
    elif remainder == 2:
        return f'{i}nd'
    elif remainder == 3:
        return f'{i}rd'
    else:
        return f'{i}th'
