from django import template
from django.core.urlresolvers import reverse

register = template.Library()

@register.simple_tag
def award_badge_link(badge, user):
  if badge.allows_award_to(user):
    return u'<a class="award_badge" href="%s">%s</a>' % ( reverse('minibadge.award_badge', args=[badge.slug,]), 'Issue award')
  else:
    return u''