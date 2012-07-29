from django.conf.urls import patterns, url

from minibadge.views import BadgeListView, BadgeDetailView, AwardBadgeView

urlpatterns = patterns('minibadge.views',
  url(r'^$', BadgeListView.as_view(), name="minibadge.badge_list"),
  url(r'^badge/(?P<slug>[^/]+)$', BadgeDetailView.as_view(), name="minibadge.badge_detail"),
  url(r'^badge/(?P<slug>[^/]+)/award$', AwardBadgeView.as_view(), name="minibadge.award_badge"),
)