from django.forms import ModelForm

from main.models import FileInput, Campaign


class FileInputForm(ModelForm):
    class Meta:
        error_css_class = 'error'
        required_css_class = 'required'

        model = FileInput
        fields = ['file_transactions',
                  'file_goods',
                  'file_customers', 'min_support', 'min_conf', 'clusters']


class CampignForm(ModelForm):
    class Meta:
        error_css_class = 'error'
        required_css_class = 'required'

        model = Campaign
        fields = ['phone_cost', 'sms_cost', 'email_cost', 'phone_percent', 'sms_percent', 'email_percent',
                  'calls_limit', 'budget', 'cheque_up', 'min', 'sale']
