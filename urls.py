from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from web_project.views import SystemView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("analysis/", include("apps.analysis.urls")),
    path("profile/", include("apps.profile.urls")),
    path("", include("auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
