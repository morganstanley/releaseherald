{% for version in news %}
{# ================ version header ================ #}

## {{ version.version }} ({{ version.date.strftime("%Y-%m-%d") }})

{# ================ version content ================ #}
{% for news_item in version.news %}
{% if news_item.content|length >0 %}
- {{ news_item.content | indent(width=4, first=False)}}

{% endif %}
{% endfor %}

{% endfor %}
