from django import forms

class AwardBadgeForm(forms.Form):
  emails = forms.CharField(widget=forms.Textarea, label="Emails, comma separated")