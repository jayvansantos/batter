from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', TemplateView.as_view(template_name='index.html'), name="home"),

    # Examples:
    # url(r'^$', 'batter.views.home', name='home'),
    # url(r'^batter/', include('batter.foo.urls')),
    url(r'^accounts/', include('userena.urls')),
    url(r"^notifications/", include("notifications.urls")),
    url(r'^torrents/', include("torrents.urls")),
    url(r'^music/', include("music.urls")),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
