from .models import Review
from django.forms import ModelForm, TextInput, Textarea, DateField
from .models import Order


class OrderForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["order_date"].label = "Дата получения заказа"

    order_date = DateField(widget=TextInput(attrs={"type": "date"}))

    class Meta:
        model = Order
        fields = (
            "first_name", "last_name", "phone", "address", "buying_type", "order_date", "comments"
        )


class ReviewForm(ModelForm):
    class Meta:
        model = Review
        fields = ["title", "reviews"]
        widgets = {
            "title": TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter text"
            }),
            "reviews": Textarea(attrs={
                "class": "form-control",
                "placeholder": "Enter a description"
            })
        }
