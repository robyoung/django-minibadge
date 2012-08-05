import base64
from datetime import datetime
import hashlib
import uuid
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.context import RequestContext
from django.template.loader import render_to_string
import os
from urlparse import urljoin
from time import time
import random

from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

OBI_VERSION = "0.5.0"
BADGE_ISSUER = getattr(settings, "MINIBADGE_ISSUER")

UPLOADS_ROOT = getattr(settings, 'MINIBADGE_UPLOADS_ROOT',
  os.path.join(getattr(settings, 'MEDIA_ROOT', 'media/'), 'uploads'))
UPLOADS_URL = getattr(settings, 'MINIBADGE_UPLOADS_URL',
  urljoin(getattr(settings, 'MEDIA_URL', '/media/'), 'uploads/'))
BADGE_UPLOADS_FS = FileSystemStorage(location=UPLOADS_ROOT,
  base_url=UPLOADS_URL)

MK_UPLOAD_TMPL = '%(base)s/%(field_fn)s_%(slug)s_%(now)s_%(rand)04d.%(ext)s'

def mk_upload_to(field_fn, ext, tmpl=MK_UPLOAD_TMPL):
  """upload_to builder for file upload fields"""
  def upload_to(instance, filename):
    base, slug = instance.get_upload_meta()
    return tmpl % dict(now=int(time()), rand=random.randint(0, 1000),
      slug=slug[:50], base=base, field_fn=field_fn,
      ext=ext)
  return upload_to

def _truncate(content, length=128):
  if len(content) <= length:
    return content
  else:
    return ' '.join(content[:length+1].split(' ')[:-1])

class BadgeManager(models.Manager):
  pass

class Badge(models.Model):
  objects = BadgeManager()

  title = models.CharField(max_length=255, blank=False, unique=True,
    help_text="Short, descriptive title")
  slug = models.SlugField(blank=False, unique=True,
    help_text="Very short name, for use in URLs and links")
  description = models.TextField(blank=True,
    help_text="Longer description of the badge and its criteria")
  image = models.ImageField(blank=True, null=True,
    storage=BADGE_UPLOADS_FS, upload_to=mk_upload_to('image','png'),
    help_text="Upload an image to represent the badge")
  creator = models.ForeignKey(User, blank=True, null=True)

  created_at = models.DateTimeField(auto_now_add=True, blank=False)
  updated_at = models.DateTimeField(auto_now=True, blank=False)

  def get_upload_meta(self):
    return ("badge", self.slug)

  def get_absolute_url(self):
    return reverse('minibadge.badge_detail', args=(self.slug,))

  def allows_award_to(self, user):
    if None == user:
      return True
    if user.is_anonymous():
      return False
    if user.is_staff or user.is_superuser:
      return True
    if user == self.creator:
      return True

    return False

  def as_obi_serialization(self, request=None):
    """Produce an Open Badge Infrastructure serialization of this badge"""
    if request:
      base_url = request.build_absolute_uri('/')[:-1]
    else:
      base_url = 'http://%s' % (Site.objects.get_current().domain,)

    # this differs from Badger as we only have a single issuer and we must have an image
    return {
      "version": OBI_VERSION,
      "name": _truncate(self.title, 128),
      "description": _truncate(self.description, 128),
      # todo: should it be possible to set up the criteria url as somewhere else?
      "criteria": urljoin(base_url, self.get_absolute_url()),
      # todo: should some of this be provided by the creator model?
      "issuer": BADGE_ISSUER,
      "image": urljoin(base_url, self.image.url)
    }


class AwardManager(models.Manager):
  pass

class Award(models.Model):
  objects = AwardManager()

  badge = models.ForeignKey(Badge)
  email = models.EmailField(blank=False, db_index=True)
  slug  = models.CharField(max_length=5, blank=False, unique=True)

  created_at = models.DateTimeField(auto_now_add=True, blank=False)
  updated_at = models.DateTimeField(auto_now=True, blank=False)

  def __str__(self):
    return "Award of %s to %s" % (self.badge.title, self.email)

  def get_absolute_url(self, format="json"):
    return reverse("minibadge.assertion.%s" % format, args=(self.slug,))

  def get_claim_url(self, request=None):
    if request:
      base_url = request.build_absolute_uri('/')[:-1]
    else:
      base_url = 'http://%s' % (Site.objects.get_current().domain,)

    return "%s/%s" % (base_url, self.email)

  def get_new_slug(self):
    m = hashlib.md5()
    m.update("%s%s" % (datetime.now(), self.email))
    slug = base64.urlsafe_b64encode(m.digest()).rstrip("=")[:5]
    # check the slug isn't already taken
    if len(Award.objects.filter(slug=slug)):
      return self.get_new_slug()
    return slug

  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = self.get_new_slug()
    return super(Award, self).save(*args, **kwargs)

  def as_obi_assertion(self, request=None):
    badge_data = self.badge.as_obi_serialization(request)

    if request:
      base_url = request.build_absolute_uri('/')[:-1]
    else:
      base_url = 'http://%s' % (Site.objects.get_current().domain,)

    recipient, salt = self._get_recipient()

    return {
      "recipient": recipient,
      "salt": salt,
      # todo: should we allow something custom?
      "evidence": urljoin(base_url, self.get_absolute_url()),
      "issued_on": self.created_at.strftime('%Y-%m-%d'),
      "badge": badge_data
    }

  def _get_recipient(self):
    hash_salt = hashlib.md5("%s%s" % (uuid.uuid4(), self.pk)).hexdigest()

    recipient_text = '%s%s' % (self.email, hash_salt)
    recipient_hash = 'sha256$%s' % hashlib.sha256(recipient_text).hexdigest()

    return recipient_hash, hash_salt

  def send(self):
    context = {"badge": self.badge, "award": self}
    body = render_to_string("minibadge/award_email.txt", {}, context)
    send_mail("You've achieved a YRS badge!", body, settings.DEFAULT_FROM_EMAIL,
      [self.email], fail_silently=True
    )