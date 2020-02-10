from django.template.defaulttags import register

""" Note that these tags were registered in config.settings.base in the TEMPLATES section under libraries """


@register.filter
def format_dv(val):
    # Since dv values are stored from 0 to 1 in the database, *100 and append "%" to make values more readable
    if val is not None and val is not '':
        return f"{int(val * 100)} %"
    else:
        return ""


@register.filter
def format_nutrient_value(val):
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
