import base64
from datetime import datetime
import hashlib
from django.core.urlresolvers import reverse
import os
from urlparse import urljoin
from time import time
import random

from django.conf import settings
from django.db import models
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User


UPLOADS_ROOT = getattr(settings, 'BADGER_UPLOADS_ROOT',
  os.path.join(getattr(settings, 'MEDIA_ROOT', 'media/'), 'uploads'))
UPLOADS_URL = getattr(settings, 'BADGER_UPLOADS_URL',
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


class AwardManager(models.Manager):
  pass

# TODO: needs hash on creation to use in url
class Award(models.Model):
  objects = AwardManager()

  badge = models.ForeignKey(Badge)
  email = models.EmailField(blank=False, db_index=True)
  slug  = models.CharField(max_length=5, blank=False, unique=True)

  created_at = models.DateTimeField(auto_now_add=True, blank=False)
  updated_at = models.DateTimeField(auto_now=True, blank=False)

  def __str__(self):
    return "Award of %s to %s" % (self.badge.title, self.email)

  # TODO: needs to actually return a full url
  def get_assertion_url(self):
    return reverse("minibadge.assertion", args=(self.slug,))

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