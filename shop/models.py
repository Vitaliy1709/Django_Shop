from PIL import Image
import sys

from django.db import models
from django.core.validators import MaxLengthValidator

from django.contrib.auth import get_user_model

from django.urls import reverse

from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

User = get_user_model()


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get("with_respect_to")
        products = []
        products_models = LightMotor.objects.all().filter(model__in=args)
        for products_model in products_models:
            model_products = products_model.objects.all().model_class()._base_manager.all().order_by("-id")[5]
            products.extend(model_products)
        if with_respect_to:
            products_model = LightMotor.objects.filter(model=with_respect_to)
            if products_model.exists():
                if with_respect_to in args:
                    return sorted(
                        products, key=lambda x: x.__class__._meta.model_name.startswith(with_respect_to), reverse=True
                    )
        return products


class LatestProducts:
    objects = LatestProductsManager()


class Category(models.Model):
    name = models.CharField("Category", max_length=200, db_index=True)
    slug = models.SlugField(max_length=200, db_index=True, unique=True)

    categories = {
        "LightMotor": "light_motors",
        "CommercialVehicles": "commercial_vehicles"
    }

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("name",)
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("category_detail", args=[str(self.id)], kwargs={"slug": self.slug})


class Product(models.Model):
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (800, 800)
    MAX_IMAGE_SIZE = 3145728

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name="категория транспорта", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="наименование", db_index=True)
    vendor_code = models.CharField(max_length=6, verbose_name="артикул", unique=True, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    image = models.ImageField(verbose_name="изображение", blank=True)
    description = models.TextField(verbose_name="описание продукта", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="цена")
    available = models.BooleanField(verbose_name="в наличии", default=True)
    created = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def get_model_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        ordering = ("title",)
        index_together = (("id", "slug"),)

        def __str__(self):
            return f"{self.ordering}: {self.index_together}"

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_height, min_width = self.MIN_RESOLUTION
        max_height, max_width = self.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorException("Разрешение изображения меньше минимального!")
        if img.height > max_height or img.width > max_width:
            raise MaxResolutionErrorException("Разрешение изображения больше максимального!")

        image = self.image
        img = Image.open(image)
        new_img = img.convert("RGB")
        resized_new_img = new_img.resize((500, 500), Image.ANTIALIAS)
        filestream = BytesIO()
        resized_new_img.save(filestream, "JPEG", quality=90)
        filestream.seek(0)
        name = "{}.{}".format(*self.image.name.split("."))
        self.image = InMemoryUploadedFile(
            filestream, "ImageField", name, "jpeg/image", sys.getsizeof(filestream), None
        )
        super().save(*args, **kwargs)


class LightMotor(Product):
    product_group = models.CharField(max_length=200, verbose_name="группа продукта")
    composition = models.CharField(max_length=200, verbose_name="состав продукта", blank=True)
    viscosity = models.CharField(max_length=6, verbose_name="вязкость продукта")
    volume = models.CharField(max_length=6, verbose_name="объем", blank=True)
    classification = models.CharField(max_length=200, verbose_name="классификация продукта", blank=True)
    manufacturer_approval = models.CharField(max_length=200, verbose_name="одобрение производителей", blank=True)
    under_a_specific_brand = models.BooleanField(verbose_name="под конкретную модель", default=False)
    brand = models.CharField(max_length=50, verbose_name="марка автомобиля", null=True, blank=True)
    year_of_issue = models.DateField(verbose_name="год выпуска", null=True, blank=True)

    def __str__(self):
        return f"{self.category.name}:{self.title}"

    def get_absolute_url(self):
        return reverse(self, "light_motors", args=[str(self.id)])


class CommercialVehicles(Product):
    product_group = models.CharField(max_length=200, verbose_name="группа продукта")
    composition = models.CharField(max_length=200, verbose_name="состав продукта", blank=True)
    viscosity = models.CharField(max_length=6, verbose_name="вязкость продукта")
    volume = models.CharField(max_length=6, verbose_name="объем", blank=True)
    classification = models.CharField(max_length=200, verbose_name="классификация продукта", blank=True)
    manufacturer_approval = models.CharField(max_length=200, verbose_name="одобрение производителей", blank=True)

    def __str__(self):
        return f"{Product.vendor_code} {Product.title}"


class ProductCart(models.Model):
    user = models.ForeignKey("Customer", verbose_name="покупатель", on_delete=models.CASCADE)
    cart = models.ForeignKey("Cart", verbose_name="корзина", related_name="related_products",
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name="количество", default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="общая сумма")

    def __str__(self):
        return f"Продукт (для корзины): {self.product.title}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey("Customer", verbose_name="владелец", null=True, on_delete=models.CASCADE)
    product = models.ManyToManyField(ProductCart, verbose_name="продукт", related_name="related_cart", blank=True)
    total_products = models.PositiveIntegerField(verbose_name="количество", default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="общая сумма", default=0)
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return f"{self.owner}. Заказ № {str(self.id)}."


class Customer(models.Model):
    user = models.ForeignKey(User, verbose_name="пользователь", related_name="related_name",
                             on_delete=models.CASCADE)
    phone = models.CharField(max_length=13, null=True, blank=True, verbose_name="номер телефона")
    address = models.CharField(max_length=200, null=True, blank=True, verbose_name="адрес доставки")
    orders = models.ManyToManyField("Order", verbose_name="заказы покупателя", related_name="related_customer")

    def __str__(self):
        return f"Покупатель: {self.user}"


class Order(models.Model):
    STATUS_NEW = "new"
    STATUS_PROGRESS = "in_progress"
    STATUS_READY = "is_ready"
    STATUS_COMPLETED = "completed"

    BUYING_TYPE_SELF = "self"
    BUYING_TYPE_DELIVERY = "delivery"

    STATUS_CHOICES = (
        (STATUS_NEW, "Новый заказ"),
        (STATUS_PROGRESS, "Заказ в обработке"),
        (STATUS_READY, "Заказ готов"),
        (STATUS_COMPLETED, "Заказ выполнен")
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, "Самовывоз"),
        (BUYING_TYPE_DELIVERY, "Доставка")
    )

    customer = models.ForeignKey("Customer", verbose_name="покупатель", related_name="related_orders",
                                 on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255, verbose_name="имя")
    last_name = models.CharField(max_length=255, verbose_name="фамилия")
    phone = models.CharField(max_length=13, verbose_name="номер телефона")
    address = models.CharField(max_length=1024, null=True, blank=True, verbose_name="адрес доставки")
    cart = models.ForeignKey(Cart, verbose_name="корзина", null=True, blank=True, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=100,
        verbose_name="статус заказа",
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name="тип заказа",
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_SELF
    )

    comments = models.TextField(verbose_name="комментарий к заказу", null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="дата создания заказа", auto_now=True)
    order_data = models.DateField(verbose_name="дата получения заказа", default=timezone.now)

    def __str__(self):
        return str(self.id)


class Slider(models.Model):
    name = models.CharField(max_length=100, validators=[MaxLengthValidator(100)],
                            error_messages={"max_length": "Очень большая длина"},
                            help_text="просто название слайда до 100 символов, оно обязательно",
                            verbose_name="название слайда")
    title = models.CharField(blank=True, max_length=150, validators=[MaxLengthValidator(150)],
                             error_messages={"max_length": "Очень большая длина"},
                             help_text="до 150 символов, заполнять необязательно",
                             verbose_name="заголовок на слайде")
    description = models.CharField(blank=True, max_length=150, validators=[MaxLengthValidator(150)],
                                   error_messages={"max_length": "Очень большая длина"},
                                   help_text="до 150 символов, заполнять необязательно",
                                   verbose_name="текст под заголовком")
    slide_img = models.ImageField(blank=False, upload_to="slider/",
                                  help_text="изображение обрежется до 1920x1024px",
                                  verbose_name="добавить изображение")

    class Meta:
        verbose_name = "блок 1.0: Слайдер"
        verbose_name_plural = "блок 1.0: Слайдеры"

    def __str__(self):
        return self.name


class Review(models.Model):
    title = models.CharField("Title", max_length=50)
    reviews = models.TextField("Reviews", max_length=255)

    class Meta:
        verbose_name = "review"
        verbose_name_plural = "reviews"

    def __str__(self):
        return self.title
