from django import template
from shop.models import Slider

register = template.Library()


@register.inclusion_tag("shop/widget_slider_home_page.html")
def block_slider():
    slider_block = Slider.objects.all()
    return {"slider_block": slider_block}
