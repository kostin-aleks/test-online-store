"""online_store URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from django.urls import include, path, re_path

from rest_framework.permissions import AllowAny

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def health_check(request):
    return HttpResponse(status=200)


schema_view = get_schema_view(
    openapi.Info(
        title="Online Store API",
        default_version='v1',
        description="""
Welcome to the Online Store API (ver. 1.0) documentation

For authorization, use the login API method.
Use the "Authorize" button.
In the value field, enter the access value with the prefix "Bearer",
e.g. "Bearer eyJhbGciOiJCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVm.zI1NiIsInR5cCI6IkpXVCJ9"
""",
    ),
    public=True,
    permission_classes=(AllowAny,),
    patterns=[path("", include('online_store.urls'))],
)


urlpatterns = [
    path('', health_check),
    path("admin/", admin.site.urls),

    path("docs/", schema_view.with_ui('swagger', cache_timeout=0), name="schema-swagger"),
    path('auth/', include('online_store.accounts.auth-urls')),
    path('accounts/', include('online_store.accounts.urls')),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.autodiscover()
admin.site.site_header = "Online Store Admin"
admin.site.site_title = "Online Store Site"
admin.site.index_title = "Online Store Site"
