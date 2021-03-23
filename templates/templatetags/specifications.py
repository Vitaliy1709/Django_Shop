from django import template
from django.utils.safestring import mark_safe

from shop.models import LightMotor

register = template.Library()

TABLE_HEAD = """
                <table class="table">
                  <tbody>
             """

TABLE_TAIL = """
                  </tbody>
                </table>

            """

TABLE_CONTENT = """
                <tr>
                  <td>{name}</td>
                  <td>{value}</td>
                </tr>
                """

PRODUCT_SPEC = {
    "light_motor": {
        "Группа продукта": "product_group",
        "Состав продукта": "composition",
        "Вязкость продукта": "viscosity",
        "Объем": "volume",
        "Классификация продукта": "classification",
        "Одобрение производителей": "manufacturer_approval",
        "Под конкретную модель": "under_a_specific_brand",
        "Марка автомобиля": "brand",
        "Год выпуска": "year_of_issue",

    },
    "commercial_vehicles": {
        "Группа продукта": "product_group",
        "Состав продукта": "composition",
        "Вязкость продукта": "viscosity",
        "Классификация продукта": "classification",
        "Одобрение производителей": "manufacturer_approval",
        "Объем": "volume"
    }
}


def get_product_spec(product, model_name):
    table_content = ""
    for name, value in PRODUCT_SPEC[model_name].items():
        table_content += TABLE_CONTENT.format(name=name, value=getattr(product, value))
    return table_content


@register.filter
def product_spec(product):
    model_name = product.__class__._meta.model_name
    if isinstance(product, LightMotor):
        if not product.under_a_specific_brand:
            PRODUCT_SPEC["light_motor"].pop("Марка автомобиля")
            PRODUCT_SPEC["light_motor"].pop("Год выпуска")
        else:
            PRODUCT_SPEC["light_motor"]["Марка автомобиля"] = "brand"
            PRODUCT_SPEC["light_motor"]["Год выпуска"] = "year_of_issue"
        return mark_safe(TABLE_HEAD + get_product_spec(product, model_name) + TABLE_TAIL)
