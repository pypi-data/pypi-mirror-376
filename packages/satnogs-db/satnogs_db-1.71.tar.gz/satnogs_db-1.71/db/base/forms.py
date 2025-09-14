"""SatNOGS DB django base Forms class"""
from bootstrap_modal_forms.forms import BSModalForm, BSModalModelForm
from django.core.exceptions import ValidationError
from django.forms import ModelChoiceField, ModelForm, Select, TextInput
from django.utils.translation import gettext_lazy as _

from db.base.models import Satellite, SatelliteEntry, Transmitter, TransmitterEntry


def existing_uuid(value):
    """ensures the UUID is existing and valid"""
    try:
        Transmitter.objects.get(uuid=value)
    except Transmitter.DoesNotExist as error:
        raise ValidationError(
            _('%(value)s is not a valid uuid'),
            code='invalid',
            params={'value': value},
        ) from error


transmitter_form_fields = [
    'description', 'type', 'status', 'uplink_low', 'uplink_high', 'uplink_drift', 'uplink_mode',
    'downlink_low', 'downlink_high', 'downlink_drift', 'downlink_mode', 'invert', 'baud',
    'citation', 'service', 'iaru_coordination', 'iaru_coordination_url', 'itu_notification',
    'unconfirmed', 'receive_review_update'
]
transmitter_form_labels = {
    'downlink_low': _('Downlink freq.'),
    'uplink_low': _('Uplink freq.'),
    'invert': _('Inverted Transponder'),
    'iaru_coordination': _('IARU Coordination'),
    'iaru_coordination_url': _('IARU Coordination URL'),
    'itu_notification': _('ITU Notifications URLs'),
    'receive_review_update': _('Email me when reviewed')
}
transmitter_form_widgets = {
    'description': TextInput(),
    'invert': Select(choices=((False, 'No'), (True, 'Yes'))),
    'unconfirmed': Select(choices=((False, 'No'), (True, 'Yes'))),
    'receive_review_update': Select(choices=((False, 'No'), (True, 'Yes')))
}


class TransmitterCreateForm(BSModalModelForm):  # pylint: disable=too-many-ancestors
    """Model Form class for TransmitterEntry objects"""

    class Meta:
        model = TransmitterEntry
        fields = transmitter_form_fields
        labels = transmitter_form_labels
        widgets = transmitter_form_widgets


class TransmitterSuggestionModifyForm(ModelForm):
    """Form used to modify submitted transmitter suggestions"""

    class Meta:
        model = TransmitterEntry
        fields = transmitter_form_fields
        labels = transmitter_form_labels
        widgets = transmitter_form_widgets


class TransmitterUpdateForm(BSModalModelForm):  # pylint: disable=too-many-ancestors
    """Model Form class for TransmitterEntry objects"""

    class Meta:
        model = TransmitterEntry
        fields = transmitter_form_fields
        labels = transmitter_form_labels
        widgets = transmitter_form_widgets


satellite_form_fields = [
    'norad_cat_id', 'norad_follow_id', 'name', 'names', 'description', 'operator', 'status',
    'countries', 'website', 'dashboard_url', 'launched', 'deployed', 'decayed', 'image',
    'citation', 'receive_review_update'
]

satellite_form_labels = {
    'norad_cat_id': _('Norad ID'),
    'norad_follow_id': _('Followed Norad ID'),
    'names': _('Other names'),
    'countries': _('Countries of Origin'),
    'launched': _('Launch Date'),
    'deployed': _('Deploy Date'),
    'decayed': _('Re-entry Date'),
    'description': _('Description'),
    'dashboard_url': _('Dashboard URL'),
    'operator': _('Owner/Operator'),
    'receive_review_update': _('Email me when reviewed')
}

satellite_form_widgets = {
    'names': TextInput(),
    'receive_review_update': Select(choices=((False, 'No'), (True, 'Yes')))
}


class SatelliteCreateForm(BSModalModelForm):  # pylint: disable=too-many-ancestors
    """Form that uses django-bootstrap-modal-forms for satellite editing"""

    class Meta:
        model = SatelliteEntry
        fields = satellite_form_fields
        labels = satellite_form_labels
        widgets = satellite_form_widgets


class SatelliteSuggestionModifyForm(ModelForm):  # pylint: disable=too-many-ancestors
    """Form that uses django-bootstrap-modal-forms for satellite editing"""

    class Meta:
        model = SatelliteEntry
        fields = satellite_form_fields
        labels = satellite_form_labels
        widgets = satellite_form_widgets


class SatelliteUpdateForm(BSModalModelForm):  # pylint: disable=too-many-ancestors
    """Form that uses django-bootstrap-modal-forms for satellite editing"""

    class Meta:
        model = SatelliteEntry
        fields = satellite_form_fields
        labels = satellite_form_labels
        widgets = satellite_form_widgets


class MergeSatellitesForm(BSModalForm):
    """Form that uses django-bootstrap-modal-forms for merging satellites"""
    primary_satellite = ModelChoiceField(
        label=_('Primary Satellite'),
        queryset=Satellite.objects.filter(
            associated_satellite__isnull=True, satellite_entry__approved=True
        ),
        empty_label="Select the Primary Satellite"
    )
    associated_satellite = ModelChoiceField(
        label=_('Associated Satellite'),
        queryset=Satellite.objects.filter(
            associated_satellite__isnull=True, satellite_entry__approved=True
        ),
        empty_label="Select the Associated Satellite"
    )

    def clean(self):
        if any(self.errors):
            # If there are errors in forms validation no need for validating the formset
            return

        cleaned_data = super().clean()
        primary_satellite = cleaned_data.get("primary_satellite")
        associated_satellite = cleaned_data.get("associated_satellite")

        if primary_satellite == associated_satellite:
            self.add_error(
                'associated_satellite',
                ValidationError(
                    _('Associated Satellite can not be the same with the Primary Satellite'),
                    code='invalid'
                )
            )

    class Meta:
        fields = ['primary_satellite', 'associated_satellite']
