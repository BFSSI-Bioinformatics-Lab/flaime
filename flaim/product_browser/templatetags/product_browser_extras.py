from django.template.defaulttags import register

""" Note that these tags were registered in config.settings.base in the TEMPLATES section under libraries """


@register.filter
def render_atwater(val: str) -> str:
    failed = ['Investigation Required']
    warning = ['Missing Information']
    passed = ['Within Threshold', 'High Fiber', 'Contains Substitute']
    html = 'N/A'
    if val in failed:
        html = f'<div><div class="text-danger">Fail <i class="far fa-times-circle"></i></div>({val})</div>'
    elif val in warning:
        html = f'<div class="text-warning">{val} <i class="far fa-question-circle"></i></div>'
    elif val in passed:
        html = f'<div><div class="text-success">Pass <i class="far fa-check-circle"></i></div>({val})</div>'
    return html


@register.filter
def render_breadcrumbs(val: str) -> str:
    if val is None:
        return ''
    breadcrumbs = ['<btn class="btn btn-sm btn-primary">' + x + '</btn>' for x in val][:-1]
    breadcrumbs_pretty = ' <strong>></strong> '.join(breadcrumbs)
    return breadcrumbs_pretty


@register.filter
def render_breadcrumbs_walmart(val: str) -> str:
    if val is None:
        return ''
    breadcrumbs = val.split('>')
    breadcrumbs = ['<btn class="btn btn-sm btn-primary">' + x + '</btn>' for x in breadcrumbs]
    breadcrumbs_pretty = ' <strong>></strong> '.join(breadcrumbs)
    return breadcrumbs_pretty


@register.filter
def render_ingredients(val: str) -> str:
    if val is not None:
        return val.title()
    return "N/A"


@register.filter
def format_dv(val: str) -> str:
    # Since dv values are stored from 0 to 1 in the database, *100 and append "%" to make values more readable
    if val is not None and val is not '':
        return f"{int(val * 100)} %"
    else:
        return ""


@register.filter
def format_nutrient_value(val: str) -> str:
    # Since the data is stored strictly as g in the database; if the value is less than 1, convert to milligrams
    if val is not None and val is not '':
        if val < 1:
            return f"{int(val * 1000)} mg"
        else:
            if float(val).is_integer():
                return f"{int(val)} g"
            else:
                return f"{float(val):1} g"
    else:
        return ""
