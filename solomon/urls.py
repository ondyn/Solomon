"""
Solomon — URL configuration.

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
]

# i18n-prefixed URL patterns
urlpatterns += i18n_patterns(
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    # Authentication
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "accounts/password_change/",
        auth_views.PasswordChangeView.as_view(template_name="registration/password_change.html"),
        name="password_change",
    ),
    path(
        "accounts/password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(template_name="registration/password_change_done.html"),
        name="password_change_done",
    ),
    # App modules
    path("buildings/", include("buildings.urls")),
    path("flats/", include("flats.urls")),
    path("owners/", include("owners.urls")),
    path("tenants/", include("tenants.urls")),
    path("accounts/users/", include("accounts.urls")),
    path("", include("core.urls")),
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    try:
        import debug_toolbar  # noqa: F401

        urlpatterns += [
            path("__debug__/", include("debug_toolbar.urls")),
        ]
    except ImportError:
        pass
