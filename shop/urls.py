from django.urls import path
from . import views


urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("product/", views.ProductDetailView.as_view(), name="product_detail"),
    path("category/", views.CategoryDetailView.as_view(), name="category_detail"),
    path("create/", views.create_feedback, name="create"),
    path("feedback/", views.review, name="feedback"),
    path("cart/", views.CartView.as_view(), name="cart"),
    path("light_motors/", views.LightMotorDetailView.as_view(), name="light_motor-specification"),
    path("add_to_cart/<str:slug>/", views.AddToCartView.as_view(), name="add_to_cart"),
    path("remove_from_cart/<str:slug>/", views.DeleteFromCartView.as_view(), name="delete_from_cart"),
    path("change_quantity/<str:slug>/", views.ChangeQuantityView.as_view(), name="change_quantity"),
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("make_order/", views.MakeOrderView.as_view(), name="make_order"),
]
