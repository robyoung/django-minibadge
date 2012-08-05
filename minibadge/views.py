import json
from urlparse import urljoin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from minibadge.forms import AwardBadgeForm
from minibadge.models import Badge, Award
import minibadge.mailer

class BadgeListView(ListView):
  template_name = 'minibadge/badge_list.html'
  model = Badge
  queryset = Badge.objects.order_by('-updated_at').all()

class BadgeDetailView(DetailView):
  template_name = 'minibadge/badge_detail.html'
  model = Badge

class AwardBadgeView(DetailView):
  template_name = 'minibadge/award_badge.html'
  model = Badge

  def post(self, *args, **kwargs):
    return self.get(*args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(AwardBadgeView, self).get_context_data(**kwargs)

    if self.request.method == "POST":
      form = AwardBadgeForm(self.request.POST)
      if form.is_valid():
        emails = form.cleaned_data['emails'].split(',')
        badge = context['badge']
        awards = []
        awards += list(Award.objects.filter(badge=badge, email__in=emails))
        for email in set(emails) - set(award.email for award in awards):
          awards.append(Award.objects.create(badge=badge, email=email))

        # send emails
        for email in set(award.email for award in awards):
          minibadge.mailer.send(email)

        return HttpResponseRedirect("/")
    else:
      form = AwardBadgeForm()

    context['form'] = form
    return context

  @method_decorator(login_required)
  def dispatch(self, *args, **kwargs):
    return super(AwardBadgeView, self).dispatch(*args, **kwargs)

class ClaimBadgesView(TemplateView):
  template_name = "minibadge/claim_badges.html"

  def get_context_data(self, email):
    context = super(ClaimBadgesView, self).get_context_data(email=email)
    context['awards'] = json.dumps([self.award_url(award) for award in self.awards(email)])

    return context

  def awards(self, email):
    return Award.objects.filter(email=email)

  def award_url(self, award):
    return urljoin(self.request.build_absolute_uri('/')[:-1], award.get_absolute_url("json"))

class AssertionView(TemplateView):
  template_name = "minibadge/award_detail.html"
  format = None

  def __init__(self, format, **kwargs):
    super(AssertionView, self).__init__(**kwargs)
    self.format = format

  def get(self, request, slug):
    award = get_object_or_404(Award, slug=slug)

    if self.format == "json":
      assertion = award.as_obi_assertion(request)
      return HttpResponse(json.dumps(assertion), mimetype="application/json")
    else:
      return self.render_to_response({
        "params": {"slug": slug},
        "award": award
      })
