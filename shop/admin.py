from django.contrib import admin
from .models import *
from django.forms import ModelChoiceField, ModelForm, ValidationError

from django.utils.safestring import mark_safe
from PIL import Image


@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ("title",)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


class LightMotorAdminForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance")
        if not self.instance.under_a_specific_brand:
            self.fields["brand"].widget.attrs.update({
                "readonly": True, "style": "background: lightgray"
            })
            self.fields["year_of_issue"].widget.attrs.update({
                "readonly": True, "style": "background: lightgray"
            })

    def clean(self):
        if not self.cleaned_data["under_a_specific_brand"]:
            self.cleaned_data["brand"] = None
            self.cleaned_data["year_of_issue"] = None
        return self.cleaned_data

    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].help_text = mark_safe(
            """'<span style="color:red; font-size:14px;">При загрузке изображения больше {}x{}, оно будет обрезано!
            </span'""".format(*Product.MAX_RESOLUTION)
        )

    def clean_image(self):
        image = self.cleaned_data["image"]
        img = Image.open(image)
        min_height, min_width = Product.MIN_RESOLUTION
        max_height, max_width = Product.MAX_RESOLUTION
        if image.size > Product.MAX_IMAGE_SIZE:
            raise ValidationError("Размер загружаемого файла не должен превышать 3 МВ!")
        if img.height < min_height or img.width < min_width:
            raise ValidationError("Разрешение изображения меньше минимального!")
        if img.height > max_height or img.width > max_width:
            raise ValidationError("Разрешение изображения больше максимального!")
        return image


class LightMotorAdmin(admin.ModelAdmin):
    form = LightMotorAdminForm
    change_form_template = "admin/admin.html"

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field == "category":
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        return ModelChoiceField(Category.objects.filter(name="light_motors"))

    list_display = ("vendor_code", "image", "composition", "viscosity", "product_group", "classification",
                    "volume", "price", "available")
    list_filter = ["category", "vendor_code", "composition", "viscosity", "product_group", "volume", "price"]
    search_fields = ["vendor_code", "category", "composition", "viscosity", "product_group", "volume", "price",
                     "available"]


class CommercialVehiclesAdmin(admin.ModelAdmin):

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field == "category":
            return super().formfield_for_foreignkey(db_field, request, **kwargs)
        return ModelChoiceField(Category.objects.filter(name="commercial_vehicles"))

    list_display = ("vendor_code", "image", "composition", "viscosity", "product_group", "classification",
                    "volume", "price", "available")
    list_filter = ["category", "vendor_code", "viscosity", "product_group", "volume", "price"]

    search_fields = ["composition"]


admin.site.register(Category, CategoryAdmin)
admin.site.register(CommercialVehicles, CommercialVehiclesAdmin)
admin.site.register(LightMotor, LightMotorAdmin)
admin.site.register(ProductCart)
admin.site.register(Cart)
admin.site.register(Customer)
admin.site.register(Review)
admin.site.register(Order)
