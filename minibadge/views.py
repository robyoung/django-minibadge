import json
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.template.context import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView, View
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
    context['awards'] = json.dumps([award.get_assertion_url() for award in Award.objects.filter(email=email)])

    return context

class AssertionView(View):
  def get(self, request, *args, **kwargs):
    award = Award.objects.get(slug=kwargs['slug'])
    assertion = {
      "recipient": award.email,
      "badge": {
        "version": "0.0.1",
        "name": award.badge.title,
        "image": str(award.badge.image), # TODO: needs to be a full path
        "description": award.badge.description,
        "criteria": reverse('minibadge.badge_detail', args=(award.badge.slug,)),
        "issuer": {
          # TODO: move these out to django config
          "origin": "http://www.youngrewiredstate.org",
          "name": "Young Rewired State",
          "org": "Not sure what goes here", # TODO: find out what goes here
          "contact": "rob@roryoung.co.uk"
        }
      }
    }
    return HttpResponse(json.dumps(assertion), mimetype="application/json")