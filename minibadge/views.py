from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from minibadge.forms import AwardBadgeForm
from minibadge.models import Badge, Award
from django.conf import settings

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
        for award in awards:
          local_context = dict(context.items() + [('award', award)])
          body = render_to_string('minibadge/award_email.txt', {}, RequestContext(self.request, local_context))
          send_mail("You've achieved a YRS badge!", body, settings.DEFAULT_FROM_EMAIL,
            [award.email], fail_silently=False
          )

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
    context['awards'] = Award.objects.filter(email=email)

    return context