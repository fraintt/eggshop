from django import template

register = template.Library()


@register.filter
def badge_class(status):
    return f"badge badge-{status}"


@register.inclusion_tag("shop/_carton.html")
def carton(packs):
    """Renders up to 10 dots (one per pack, capped) as a little egg-carton icon."""
    dots = min(packs, 10)
    return {"dots": range(dots), "packs": packs}
