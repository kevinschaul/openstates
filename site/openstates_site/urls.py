from django.conf.urls import patterns, include
from django.conf import settings
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

template_view = TemplateView.as_view

urlpatterns = patterns('',

    # flat pages
    (r'^about/$', template_view(template_name='flat/about.html')),
    (r'^methodology/$', template_view(template_name='flat/methodology.html')),
    (r'^contributing/$',
        template_view(template_name='flat/contributing.html')),
    (r'^thanks/$', template_view(template_name='flat/thanks.html')),
    (r'^contact/$', template_view(template_name='flat/contact.html')),
    (r'^categorization/$',
        template_view(template_name='flat/categorization.html')),
    (r'^csv_downloads/$',
         template_view(template_name='flat/csv_downloads.html')),
    (r'^reportcard/$', template_view(template_name='flat/reportcard.html')),

    # api docs
    (r'^api/$', template_view(template_name='flat/api/api.html')),
    (r'^api/metadata/$',
        template_view(template_name='flat/api/metadata.html')),
    (r'^api/bills/$', template_view(template_name='flat/api/bills.html')),
    (r'^api/committees/$',
        template_view(template_name='flat/api/committees.html')),
    (r'^api/legislators/$',
        template_view(template_name='flat/api/legislators.html')),
    (r'^api/events/$', template_view(template_name='flat/api/events.html')),
    (r'^api/districts/$',
         template_view(template_name='flat/api/districts.html')),

    # locksmith & sunlightauth
    (r'^api/locksmith/', include('locksmith.mongoauth.urls')),
    (r'', include('sunlightauth.urls')),

    (r'^api/', include('billy.web.api.urls')),
    (r'^admin/', include('billy.web.admin.urls')),
    (r'^djadmin/', include(admin.site.urls)),
    (r'^', include('billy.web.public.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^404/$', 'django.views.defaults.page_not_found'),
        (r'^500/$', 'django.views.defaults.server_error'),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_ROOT,
          'show_indexes': True}))
