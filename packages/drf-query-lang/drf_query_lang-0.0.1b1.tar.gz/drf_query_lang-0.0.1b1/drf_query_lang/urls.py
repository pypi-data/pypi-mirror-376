from django.urls import path
from .views import QueryLangView

urlpatterns = [
    path("", QueryLangView.as_view(), name="query-lang-view"),
]