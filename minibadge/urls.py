from django.conf.urls import patterns, url

from minibadge.views import BadgeListView, BadgeDetailView, AwardBadgeView, ClaimBadgesView, AssertionView

urlpatterns = patterns('minibadge.views',
  url(r'^$', BadgeListView.as_view(), name="minibadge.badge_list"),
  url(r'^badge/(?P<slug>[^/]+)$', BadgeDetailView.as_view(), name="minibadge.badge_detail"),
  url(r'^badge/(?P<slug>[^/]+)/award$', AwardBadgeView.as_view(), name="minibadge.award_badge"),
  url(r'^claim/(?P<email>[^/]+)$', ClaimBadgesView.as_view(), name="minibadge.claim_badges"),
  url(r'^assertion/(?P<slug>[^/]+)\.json$', AssertionView.as_view(format="json"), name="minibadge.assertion.json"),
  url(r'^assertion/(?P<slug>[^/]+)$', AssertionView.as_view(format="html"), name="minibadge.assertion.html"),
)