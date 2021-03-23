from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.generic.detail import DetailView
from .forms import OrderForm, ReviewForm
from django.shortcuts import get_object_or_404
from .mixins import *
from django.contrib import messages
from .utils import recalc_cart


class IndexView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        customer = Customer.objects.get(user=request.user)
        cart = Cart.objects.get(owner=customer)
        categories = Category.objects.get_categories_for_left_slider()
        products = LatestProducts.objects.get_products_for_main_page("light_motors", "commercial_vehicles",
                                                                     with_respect_to="light_motors")
        context = {
            "categories": categories,
            "products": products,
            "cart": cart
        }

        return render(request, "index.html", context)


class ProductDetailView(DetailView, CartMixin, CategoryDetailMixin):

    def get(self, request, *args, **kwargs):
        template_name = "shop/product_detail.html"

        products = LightMotor.objects.all()
        context = {
            "products": products
        }
        return render(request, template_name, context)

    context_object_name = "product"

    slug_url_kwarg = "slug"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.model._meta.model_name
        context["cart"] = self.cart
        return context


def create_feedback(request):
    template_name = "shop/create.html"
    form = ReviewForm()

    error = ""
    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("feedback")
        else:
            error = "The form is not valid!"

    context = {
        "form": form,
        "error": error
    }

    return render(request, template_name, context)


def review(request):
    template_name = "shop/feedback.html"
    reviews = Review.objects.order_by("-id")[:5]

    return render(request, template_name, {"reviews": reviews})


class LightMotorSpecificationView(DetailView):
    template_name = "shop/light_motor_specification.html"
    context_object_name = "light_motors_spec"

    def get_queryset(self):
        slug_url_kwarg = "vendor_code"

        return slug_url_kwarg


class CategoryDetailView(DetailView, CartMixin, CategoryDetailMixin):
    model = Category

    def get(self, request, *args, **kwargs):
        category_slug = kwargs.get("slug")
        categories = Category.objects.all().get(slug=category_slug)
        template_name = "shop/category_detail.html"
        context = {
            "categories": categories
        }
        return render(request, template_name, context)

    def get_queryset(self):
        category = self.kwargs.get('category_slug', '')
        q = super().get_queryset()

        return q.filter(category__slug=category).select_related('category')

    def get_object(self):
        return get_object_or_404(self.queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = self.cart
        return context


class AddToCartView(CartMixin, View):
    model = LightMotor

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get("slug")
        product = LightMotor.objects.get(slug=product_slug)
        product_cart, created = ProductCart.objects.get_or_create(
            user=self.cart.owner, cart=self.cart, product_id=str(product.id)
        )

        if created:
            self.cart.product.add(product_cart)
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно добавлен.")
        return HttpResponseRedirect("/shop/cart/")


class DeleteFromCartView(CartMixin, View):
    model = LightMotor

    def get(self, request, *args, **kwargs):
        product_slug = kwargs.get("slug")
        product = LightMotor.objects.get(slug=product_slug)
        product_cart = ProductCart.objects.get(
            user=self.cart.owner, cart=self.cart, product_id=str(product.id)
        )

        self.cart.product.remove(product_cart)
        product_cart.delete()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Товар успешно удален.")
        return HttpResponseRedirect("/shop/cart/")


class ChangeQuantityView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        product_slug = kwargs.get("slug")
        product = LightMotor.objects.get(slug=product_slug)
        product_cart = ProductCart.objects.get(
            user=self.cart.owner, cart=self.cart, product=self.cart.product, product_id=product
        )
        quantity = int(request.POST.get("quantity"))
        product_cart.quantity = quantity
        product_cart.save()
        recalc_cart(self.cart)
        messages.add_message(request, messages.INFO, "Кол-во успешно изменено.")
        return HttpResponseRedirect("/shop/cart/")


class CartView(CartMixin, View):
    model = LightMotor

    def get(self, request, *args, **kwargs):
        products = LightMotor.objects.all()
        categories = Category.objects.get_categories_for_left_sidebar()
        template_name = "shop/cart.html"
        context = {
            "cart": self.cart,
            "products": products,
            "categories": categories
        }
        return render(request, template_name, context)


class CheckoutView(CartMixin, View):
    model = LightMotor

    def get(self, request, *args, **kwargs):
        products = LightMotor.objects.all()
        form = OrderForm(request.POST or None)
        categories = Category.objects.get_categories_for_left_sidebar()
        template_name = "shop/checkout.html"
        context = {
            "cart": self.cart,
            "products": products,
            "form": form,
            "categories": categories
        }
        return render(request, template_name, context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            new_order.customer = customer
            new_order.first_name = form.cleaned_data["first_name"]
            new_order.last_name = form.cleaned_data["last_name"]
            new_order.phone = form.cleaned_data["phone"]
            new_order.address = form.cleaned_data["address"]
            new_order.buying_type = form.cleaned_data["buying_type"]
            new_order.order_date = form.cleaned_data["order_date"]
            new_order.comments = form.cleaned_data["comments"]
            new_order.save()
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            customer.orders.add(new_order)
            messages.add_message(request, messages.INFO,
                                 "Спасибо за заказ! Наш менеджер свяжется с вами в ближайшее время.")

            return HttpResponseRedirect("/shop/")

        return HttpResponseRedirect("/shop/checkout/")


class LightMotorDetailView(DetailView):
    model = LightMotor

    def get(self, request, *args, **kwargs):
        light_motors = Category.objects.order_by("-id")[:5]

        template_name = "shop/light_motor-specification.html"

        context = {
            "light_motors": light_motors
        }
        return render(request, template_name, context)

    context_object_name = "light_motors"
    slug_url_kwarg = "slug"
