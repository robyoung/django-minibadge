from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from minibadge.models import Award

def send(email):
  awards = Award.objects.filter(email=email)
  context = {"awards": awards}
  subject = "You've achieved a YRS badge!"
  text_content = render_to_string("minibadge/award_email.txt", context)
  html_content = render_to_string("minibadge/award_email.html", context)

  message = EmailMultiAlternatives(subject, text_content, settings.DEFAULT_FROM_EMAIL, [email])
  message.attach_alternative(html_content, "text/html")
  message.send()
