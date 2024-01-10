from django import template
import re
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, search):
    if text is not None:
        text = str(text)
        src = re.compile(search, re.IGNORECASE)
        src_re = src.sub(f'<span class="highlight">{search}</span>', text)
    else:
        str_re = ''
    # h = text.lower()
    # value = h.replace(search, )
    #print(text,'st', value, text.replace('s', 'u'), search)
    return mark_safe(src_re)