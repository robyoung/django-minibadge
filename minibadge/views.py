from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from minibadge.models import Badge

class BadgeListView(ListView):
  template_name = 'minibadge/badge_list.html'
  model = Badge
  queryset = Badge.objects.order_by('-updated_at').all()

class BadgeDetailView(DetailView):
  template_name = 'minibadge/badge_detail.html'
  model = Badge

class AwardBadgeView(TemplateView):
  template_name = 'minibadge/award_badge.html'

  @method_decorator(login_required)
  def dispatch(self, *args, **kwargs):
    return super(AwardBadgeView, self).dispatch(*args, **kwargs)

