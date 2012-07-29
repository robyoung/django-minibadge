from django.conf import settings
from django.contrib import admin
from django.core.urlresolvers import reverse

from minibadge.models import Badge, Award

UPLOADS_URL = getattr(settings, 'BADGER_UPLOADS_URL',
  '%suploads/' % getattr(settings, 'MEDIA_URL', '/media/'))

def show_image(obj):
  img_url = "%s%s" % (UPLOADS_URL, obj.image if hasattr(obj, "image") else obj.badge.image)
  return ('<a href="%s" target="_new"><img src="%s" width="48" height="48" /></a>' %
          (img_url, img_url))
show_image.allow_tags = True
show_image.short_description = "Image"

def show_unicode(obj):
  return unicode(obj)
show_unicode.short_description = "Display"

def badge_link(self):
  url = reverse('admin:badger_badge_change', args=[self.badge.id])
  return '<a href="%s">%s</a>' % (url, self.badge)

badge_link.allow_tags = True
badge_link.short_description = 'Badge'

class BadgeAdmin(admin.ModelAdmin):
  list_display = ("id", "title", show_image, "slug", "creator", "created_at",)
  list_display_links = ('id', 'title',)
  search_fields = ("title", "slug", "image", "description",)
  prepopulated_fields = {"slug": ("title",)}

class AwardAdmin(admin.ModelAdmin):
  list_display = (show_unicode, badge_link, show_image, 'created_at', )
  fields = ('badge', 'email', )
  search_fields = ("badge__title", "badge__slug", "badge__description",)

for x in ((Badge, BadgeAdmin),
          (Award, AwardAdmin),):
  admin.site.register(*x)
