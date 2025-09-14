"""Django database model for SatNOGS DB"""
import logging
import re
from datetime import datetime
from os import path
from uuid import uuid4

import satnogsdecoders
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinLengthValidator, \
    MinValueValidator, URLValidator
from django.db import models
from django.db.models import OuterRef, Subquery
from django.utils.timezone import now
from django_countries.fields import CountryField
from markdown import markdown
from nanoid import generate
from shortuuidfield import ShortUUIDField

LOGGER = logging.getLogger('db')

DATA_SOURCES = ['manual', 'network', 'sids']
SATELLITE_STATUS = ['alive', 'dead', 'future', 're-entered']
TRANSMITTER_STATUS = ['active', 'inactive', 'invalid']
TRANSMITTER_TYPE = ['Transmitter', 'Transceiver', 'Transponder']
SERVICE_TYPE = [
    'Aeronautical', 'Amateur', 'Broadcasting', 'Earth Exploration', 'Fixed', 'Inter-satellite',
    'Maritime', 'Meteorological', 'Mobile', 'Radiolocation', 'Radionavigational',
    'Space Operation', 'Space Research', 'Standard Frequency and Time Signal', 'Unknown'
]
IARU_COORDINATION_STATUS = ['IARU Coordinated', 'IARU Declined', 'IARU Uncoordinated', 'N/A']
BAD_COORDINATIONS = ['IARU Declined', 'IARU Uncoordinated']  # 'violations'
URL_REGEX = r"(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&'\(\)\*\+,;=.]+$"
MIN_FREQ = 0
MAX_FREQ = 40000000000
MIN_FREQ_MSG = "Ensure this value is greater than or equal to 0Hz"
MAX_FREQ_MSG = "Ensure this value is less than or equal to 40Ghz"


def _name_diagnostic_plot(instance, filename):  # pylint: disable=W0613
    """Returns a path for OpticalObservation diagnostic_plot"""

    timestamp = datetime.now()
    return 'data_optical_obs/{0}/{1}/{2}/{3}/{4}'.format(
        timestamp.year, timestamp.month, timestamp.day, timestamp.hour, filename
    )


def _name_exported_frames(instance, filename):  # pylint: disable=W0613
    """Returns path for a exported frames file"""
    return path.join('download/', filename)


def _name_payload_frame(instance, filename):  # pylint: disable=W0613
    """Returns a unique, timestamped path and filename for a payload

    :param filename: the original filename submitted
    :returns: path string with timestamped subfolders and filename
    """
    today = now()
    folder = 'payload_frames/{0}/{1}/{2}/'.format(today.year, today.month, today.day)
    ext = 'raw'
    filename = '{0}_{1}.{2}'.format(filename, uuid4().hex, ext)
    return path.join(folder, filename)


class Launch(models.Model):
    """Model for tracking launches."""

    class Meta:
        verbose_name_plural = 'Launches'

    name = models.CharField(max_length=50)
    forum_thread_url = models.URLField(
        blank=True,
        null=True,
        max_length=200,
        validators=[URLValidator(schemes=['http', 'https'], regex=URL_REGEX)]
    )
    created = models.DateTimeField(default=now, help_text='Timestamp of creation/edit')
    created_by = models.ForeignKey(
        get_user_model(), related_name='created_launches', null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return self.name


class OpticalObservation(models.Model):
    """An model for SatNOGS optical observations"""
    diagnostic_plot = models.ImageField(upload_to=_name_diagnostic_plot)
    data = models.JSONField()
    start = models.DateTimeField()
    station_id = models.PositiveBigIntegerField()
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return f"Optical Observation #{str(self.id)}"

    class Meta:
        unique_together = ["start", "station_id"]


class OpticalIdentification(models.Model):
    """A Satnogs Optical Identification"""
    observation = models.ForeignKey(
        OpticalObservation, on_delete=models.CASCADE, related_name="identifications"
    )
    norad_id = models.PositiveIntegerField(blank=True, null=True)
    satellite = models.ForeignKey(
        "base.Satellite", blank=True, null=True, on_delete=models.SET_NULL
    )


class Mode(models.Model):
    """A satellite transmitter RF mode. For example: FM"""
    name = models.CharField(max_length=25, unique=True)

    class CacheOptions:  # pylint: disable=C0115,R0903
        default_cache_key = "mode"
        cache_purge_keys = ["mode"]

    def __str__(self):
        return self.name


class Operator(models.Model):
    """Satellite Owner/Operator"""
    name = models.CharField(max_length=255, unique=True)
    names = models.TextField(blank=True)
    description = models.TextField(blank=True)
    website = models.URLField(
        blank=True, validators=[URLValidator(schemes=['http', 'https'], regex=URL_REGEX)]
    )

    def __str__(self):
        return self.name


def validate_sat_id(value):
    """Validate a Satellite Identifier"""
    if not re.compile(r'^[A-Z]{4,4}(?:-\d\d\d\d){4,4}$').match(value):
        raise ValidationError(
            '%(value)s is not a valid Satellite Identifier. Satellite Identifier should have the \
             format "CCCC-NNNN-NNNN-NNNN-NNNN" where C is {A-Z} and N is {0-9}',
            params={'value': value},
        )


def generate_sat_id():
    """Generate Satellite Identifier"""
    numeric = "0123456789"
    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    first_segment = generate(uppercase, 4)
    second_segment = generate(numeric, 4)
    third_segment = generate(numeric, 4)
    fourth_segment = generate(numeric, 4)
    fifth_segment = generate(numeric, 4)
    return "{0}-{1}-{2}-{3}-{4}".format(
        first_segment, second_segment, third_segment, fourth_segment, fifth_segment
    )


def get_default_itu_notification_field():
    """Generate default value for itu_notification field of TransmitterEntry model"""
    return {'urls': []}


class SatelliteIdentifier(models.Model):
    """Model for Satellite Identifier."""
    sat_id = models.CharField(
        default=generate_sat_id, unique=True, max_length=24, validators=[validate_sat_id]
    )
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '{0}'.format(self.sat_id)


class SatelliteEntry(models.Model):
    """Model for all the satellite entries."""
    satellite_identifier = models.ForeignKey(
        SatelliteIdentifier, null=True, related_name='satellite_entries', on_delete=models.PROTECT
    )
    norad_cat_id = models.PositiveIntegerField(blank=True, null=True)
    norad_follow_id = models.PositiveIntegerField(blank=True, null=True)
    name = models.CharField(max_length=45)
    names = models.TextField(blank=True)
    description = models.TextField(blank=True)
    dashboard_url = models.URLField(
        blank=True,
        null=True,
        max_length=200,
        validators=[URLValidator(schemes=['http', 'https'], regex=URL_REGEX)]
    )
    image = models.ImageField(upload_to='satellites', blank=True, help_text='Ideally: 250x250')
    status = models.CharField(
        choices=list(zip(SATELLITE_STATUS, SATELLITE_STATUS)), max_length=10, default='alive'
    )
    decayed = models.DateTimeField(null=True, blank=True)

    # new fields below, metasat etc
    # countries is multiple for edge cases like ISS/Zarya
    countries = CountryField(blank=True, multiple=True, blank_label='(select countries)')
    website = models.URLField(
        blank=True, validators=[URLValidator(schemes=['http', 'https'], regex=URL_REGEX)]
    )
    launched = models.DateTimeField(null=True, blank=True)
    launch = models.ForeignKey(
        Launch, null=True, related_name='embarked_in', on_delete=models.SET_NULL
    )
    deployed = models.DateTimeField(null=True, blank=True)
    operator = models.ForeignKey(
        Operator,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='satellite_operator'
    )
    # Fields related to suggestion reviews
    reviewer = models.ForeignKey(
        get_user_model(),
        related_name='reviewed_satellites',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    reviewed = models.DateTimeField(blank=True, null=True, help_text='Timestamp of review')
    approved = models.BooleanField(default=False)
    review_message = models.TextField(blank=True, null=True)
    receive_review_update = models.BooleanField(
        default=False, null=True
    )  # Whether to notify user with the verdict of the review
    created = models.DateTimeField(default=now, help_text='Timestamp of creation/edit')
    created_by = models.ForeignKey(
        get_user_model(), related_name='created_satellites', null=True, on_delete=models.SET_NULL
    )
    citation = models.CharField(
        max_length=512,
        default='',
        help_text='A reference (preferrably URL) for this entry or edit',
        blank=False
    )

    class Meta:
        ordering = ['norad_cat_id']
        verbose_name_plural = 'Satellite Entries'
        unique_together = ("satellite_identifier", "reviewed")

    def get_description(self):
        """Returns the markdown-processed satellite description

        :returns: the markdown-processed satellite description
        """
        return markdown(self.description)

    def get_image(self):
        """Returns an image for the satellite

        :returns: the saved image for the satellite, or a default
        """
        if self.image and hasattr(self.image, 'url'):
            image = self.image.url
        else:
            image = settings.SATELLITE_DEFAULT_IMAGE
        return image

    @property
    def countries_str(self):
        """Returns countries for this Satellite in comma seperated string format

        :returns: countries for this Satellite in comma seperated string format
        """
        return ','.join(map(str, self.countries))

    def __str__(self):
        return '{0} - {1}'.format(self.norad_cat_id, self.name)


class SatelliteSuggestionManager(models.Manager):  # pylint: disable=R0903
    """Django Manager for SatelliteSuggestions

    SatelliteSuggestions are SatelliteEntry objects that have been
    submitted (suggested) but not yet reviewed
    """

    def get_queryset(self):
        """Returns SatelliteEntries that have not been reviewed"""
        return SatelliteEntry.objects.filter(reviewed__isnull=True)


class SatelliteSuggestion(SatelliteEntry):
    """Proxy model for unreviewed SatelliteEntry objects"""
    objects = SatelliteSuggestionManager()

    class Meta:
        proxy = True
        permissions = (
            ('approve_satellitesuggestion', 'Can approve/reject satellite suggestions'),
        )


class SatelliteManager(models.Manager):  # pylint: disable=R0903
    """Django Manager for Satellites

    Satellite objects rarely used without referencing their SatelliteIdentifier
    and SatelliteEntry foreign key fields, thus follow these relationships to
    get the related-objects data by using select_related().
    """

    def get_queryset(self):
        """Returns SatelliteEntries that have not been reviewed"""
        return super().get_queryset().select_related('satellite_identifier', 'satellite_entry')


class Satellite(models.Model):
    """ Model for the lastest satellite entry for each Satellite Identifier."""
    objects = SatelliteManager()

    satellite_identifier = models.OneToOneField(
        SatelliteIdentifier, related_name='satellite', on_delete=models.CASCADE
    )
    satellite_entry = models.ForeignKey(SatelliteEntry, null=True, on_delete=models.SET_NULL)
    associated_satellite = models.ForeignKey(
        'self', null=True, related_name='associated_with', on_delete=models.PROTECT
    )
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = (('merge_satellites', 'Can merge satellites'), )

    class CacheOptions:  # pylint: disable=C0115,R0903
        default_cache_key = "satellite"
        cache_purge_keys = ["satellite"]

    def __str__(self):
        if self.satellite_entry:
            name = self.satellite_entry.name
            norad_cat_id = self.satellite_entry.norad_cat_id
        else:
            name = '-'
            norad_cat_id = '-'
        return '{1} ({2}) | {0}'.format(self.satellite_identifier.sat_id, name, norad_cat_id)

    @property
    def transmitters(self):
        """Returns valid transmitters for this Satellite

        :returns: the valid transmitters for this Satellite
        """
        transmitters = Transmitter.objects.filter(satellite=self.id).exclude(status='invalid')
        return transmitters

    @property
    def invalid_transmitters(self):
        """Returns invalid transmitters for this Satellite

        :returns: the invalid transmitters for this Satellite
        """
        transmitters = Transmitter.objects.filter(satellite=self.id).filter(status='invalid')
        return transmitters

    @property
    def transmitter_suggestion_count(self):
        """Returns number of pending transmitter suggestions for this Satellite

        :returns: number of pending transmitter suggestions for this Satellite
        """
        pending_count = TransmitterSuggestion.objects.filter(satellite=self.id).count()
        return pending_count

    @property
    def satellite_suggestion_count(self):
        """Returns number of pending satellite suggestions for this Satellite

        :returns: number of pending satellite suggestions for this Satellite
        """
        pending_count = SatelliteSuggestion.objects.filter(
            satellite_identifier=self.satellite_identifier
        ).count()
        return pending_count

    @property
    def telemetry_data_count(self):
        """Returns number of DemodData for this Satellite

        :returns: number of DemodData for this Satellite
        """
        cached_satellite = cache.get(self.id)
        if cached_satellite:
            data_count = cached_satellite['count']
        else:
            satellites_list = list(self.associated_with.all().values_list('pk', flat=True))
            satellites_list.append(self.pk)
            data_count = DemodData.objects.filter(satellite__in=satellites_list).count()
        return data_count

    @property
    def telemetry_decoder_count(self):
        """Returns number of Telemetry objects for this Satellite

        :returns: number of Telemetry objects for this Satellite
        """
        decoder_count = Telemetry.objects.filter(satellite=self.id).exclude(decoder='').count()
        return decoder_count

    @property
    def latest_data(self):
        """Returns the latest DemodData for this Satellite

        :returns: dict with most recent DemodData for this Satellite
        """
        satellites_list = list(self.associated_with.all().values_list('pk', flat=True))
        satellites_list.append(self.pk)
        data = DemodData.objects.filter(satellite__in=satellites_list
                                        ).order_by('-id').values("timestamp", "station").first()
        if data:
            return {
                'timestamp': data["timestamp"],
                'station': data["station"],
            }
        return None

    @property
    def needs_help(self):
        """Returns a boolean based on whether or not this Satellite could
            use some editorial help based on a configurable threshold

        :returns: bool
        """
        score = 0
        if self.satellite_entry.description and self.satellite_entry.description != '':
            score += 1
        if self.satellite_entry.countries and self.satellite_entry.countries != '':
            score += 1
        if self.satellite_entry.website and self.satellite_entry.website != '':
            score += 1
        if self.satellite_entry.names and self.satellite_entry.names != '':
            score += 1
        if self.satellite_entry.launched and self.satellite_entry.launched != '':
            score += 1
        if self.satellite_entry.operator and self.satellite_entry.operator != '':
            score += 1
        if self.satellite_entry.image and self.satellite_entry.image != '':
            score += 1

        return score <= 2

    @property
    def has_bad_transmitter(self):
        """Returns a boolean based on whether or not this Satellite has a
            transmitter associated with it that is considered uncoordinated or
            otherwise bad

        :returns: bool
        """
        violation = cache.get("violator_" + self.satellite_identifier.sat_id)

        if violation is not None:
            return violation['status']

        result = False

        for transmitter in Transmitter.objects.filter(satellite=self.id).exclude(status='invalid'):
            if transmitter.bad_transmitter:
                result = True
                break
        cache.set(
            "violator_" + str(self.satellite_entry.norad_cat_id), {
                'status': result,
                'id': str(self.id)
            }, None
        )
        cache.set(
            "violator_" + self.satellite_identifier.sat_id, {
                'status': result,
                'id': str(self.id)
            }, None
        )
        for merged_satellite in self.associated_with.all():
            cache.set(
                "violator_" + merged_satellite.satellite_identifier.sat_id, {
                    'status': result,
                    'id': str(self.id)
                }, None
            )
        return result


class TransmitterEntry(models.Model):
    """Model for satellite transmitters."""
    uuid = ShortUUIDField(db_index=True)
    description = models.TextField(
        help_text='Short description for this entry, like: UHF 9k6 AFSK Telemetry'
    )
    status = models.CharField(
        choices=list(zip(TRANSMITTER_STATUS, TRANSMITTER_STATUS)),
        max_length=8,
        default='active',
        help_text='Functional state of this transmitter'
    )
    type = models.CharField(
        choices=list(zip(TRANSMITTER_TYPE, TRANSMITTER_TYPE)),
        max_length=11,
        default='Transmitter'
    )
    uplink_low = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_FREQ, message=MIN_FREQ_MSG),
            MaxValueValidator(MAX_FREQ, message=MAX_FREQ_MSG)
        ],
        help_text='Frequency (in Hz) for the uplink, or bottom of the uplink range for a \
            transponder'
    )
    uplink_high = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_FREQ, message=MIN_FREQ_MSG),
            MaxValueValidator(MAX_FREQ, message=MAX_FREQ_MSG)
        ],
        help_text='Frequency (in Hz) for the top of the uplink range for a transponder'
    )
    uplink_drift = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-99999), MaxValueValidator(99999)],
        help_text='Receiver drift from the published uplink frequency, stored in parts \
            per billion (PPB)'
    )
    downlink_low = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_FREQ, message=MIN_FREQ_MSG),
            MaxValueValidator(MAX_FREQ, message=MAX_FREQ_MSG)
        ],
        help_text='Frequency (in Hz) for the downlink, or bottom of the downlink range \
            for a transponder'
    )
    downlink_high = models.BigIntegerField(
        blank=True,
        null=True,
        validators=[
            MinValueValidator(MIN_FREQ, message=MIN_FREQ_MSG),
            MaxValueValidator(MAX_FREQ, message=MAX_FREQ_MSG)
        ],
        help_text='Frequency (in Hz) for the top of the downlink range for a transponder'
    )
    downlink_drift = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(-99999), MaxValueValidator(99999)],
        help_text='Transmitter drift from the published downlink frequency, stored in \
            parts per billion (PPB)'
    )
    downlink_mode = models.ForeignKey(
        Mode,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transmitter_downlink_entries',
        help_text='Modulation mode for the downlink'
    )
    uplink_mode = models.ForeignKey(
        Mode,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='transmitter_uplink_entries',
        help_text='Modulation mode for the uplink'
    )
    invert = models.BooleanField(
        default=False, help_text='True if this is an inverted transponder'
    )
    baud = models.FloatField(
        validators=[MinValueValidator(0)],
        blank=True,
        null=True,
        help_text='The number of modulated symbols that the transmitter sends every second'
    )
    satellite = models.ForeignKey(
        Satellite, null=True, related_name='transmitter_entries', on_delete=models.SET_NULL
    )
    citation = models.CharField(
        max_length=512,
        default='',
        help_text='A reference (preferrably URL) for this entry or edit',
        blank=False
    )
    service = models.CharField(
        choices=zip(SERVICE_TYPE, SERVICE_TYPE),
        max_length=34,
        default='Unknown',
        help_text='The published usage category for this transmitter'
    )
    iaru_coordination = models.CharField(
        choices=list(zip(IARU_COORDINATION_STATUS, IARU_COORDINATION_STATUS)),
        max_length=20,
        default='N/A',
        help_text='IARU frequency coordination status for this transmitter'
    )
    iaru_coordination_url = models.URLField(
        blank=True,
        help_text='URL for more details on this frequency coordination',
        validators=[URLValidator(schemes=['http', 'https'], regex=URL_REGEX)]
    )
    itu_notification = models.JSONField(default=get_default_itu_notification_field)
    reviewer = models.ForeignKey(
        get_user_model(),
        related_name='reviewed_transmitters',
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )
    reviewed = models.DateTimeField(blank=True, null=True, help_text='Timestamp of review')
    approved = models.BooleanField(default=False)
    review_message = models.TextField(blank=True, null=True)
    receive_review_update = models.BooleanField(
        default=False, null=True
    )  # Whether to notify user with the verdict of the review
    created = models.DateTimeField(default=now, help_text='Timestamp of creation/edit')
    created_by = models.ForeignKey(
        get_user_model(),
        related_name='created_transmitters',
        null=True,
        on_delete=models.SET_NULL
    )
    unconfirmed = models.BooleanField(default=False, null=True)

    # NOTE: future fields will need to be added to forms.py and to
    # api/serializers.py

    class CacheOptions:  # pylint: disable=C0115,R0903
        default_cache_key = "transmitter"
        cache_purge_keys = ["transmitter"]

    @property
    def bad_transmitter(self):
        """Returns a boolean that indicates whether this transmitter should be
        flagged as bad with regard to frequency coordination or rejection

        :returns: bool
        """
        if self.iaru_coordination in BAD_COORDINATIONS:
            return True
        return False

    class Meta:
        unique_together = ("uuid", "reviewed")
        verbose_name_plural = 'Transmitter entries'

    def __str__(self):
        return self.description

    def clean(self):
        if self.type == TRANSMITTER_TYPE[0]:
            if self.uplink_low is not None or self.uplink_high is not None \
                    or self.uplink_drift is not None:
                raise ValidationError("Uplink shouldn't be filled in for a transmitter")

            if self.downlink_high:
                raise ValidationError(
                    "Downlink high frequency shouldn't be filled in for a transmitter"
                )

        elif self.type == TRANSMITTER_TYPE[1]:
            if self.uplink_high is not None or self.downlink_high is not None:
                raise ValidationError("Frequency range shouldn't be filled in for a transceiver")

        elif self.type == TRANSMITTER_TYPE[2]:
            if self.downlink_low is not None and self.downlink_high is not None:
                if self.downlink_low > self.downlink_high:
                    raise ValidationError(
                        "Downlink low frequency must be lower or equal \
                        than downlink high frequency"
                    )

            if self.uplink_low is not None and self.uplink_high is not None:
                if self.uplink_low > self.uplink_high:
                    raise ValidationError(
                        "Uplink low frequency must be lower or equal \
                        than uplink high frequency"
                    )


class TransmitterSuggestionManager(models.Manager):  # pylint: disable=R0903
    """Django Manager for TransmitterSuggestions

    TransmitterSuggestions are TransmitterEntry objects that have been
    submitted (suggested) but not yet reviewed
    """

    def get_queryset(self):
        """Returns TransmitterEntries that have not been reviewed"""
        return TransmitterEntry.objects.filter(reviewed__isnull=True)


class TransmitterSuggestion(TransmitterEntry):
    """TransmitterSuggestion is an unreviewed TransmitterEntry object"""
    objects = TransmitterSuggestionManager()

    def __str__(self):
        return self.description

    class Meta:
        proxy = True
        permissions = (
            ('approve_transmittersuggestion', 'Can approve/reject transmitter suggestions'),
        )


class TransmitterManager(models.Manager):  # pylint: disable=R0903
    """Django Manager for Transmitter objects"""

    def get_queryset(self):
        """Returns query of TransmitterEntries

        :returns: the latest revision of a TransmitterEntry for each
        TransmitterEntry uuid associated with this Satellite that is
        both reviewed and approved
        """
        subquery = TransmitterEntry.objects.filter(
            reviewed__isnull=False, approved=True
        ).filter(uuid=OuterRef('uuid')).order_by('-reviewed')
        return super().get_queryset().filter(
            reviewed__isnull=False, approved=True
        ).select_related('satellite', 'downlink_mode',
                         'uplink_mode').filter(reviewed=Subquery(subquery.values('reviewed')[:1]))


class Transmitter(TransmitterEntry):
    """Associates a generic Transmitter object with their TransmitterEntries
    that are managed by TransmitterManager
    """
    objects = TransmitterManager()

    def __str__(self):
        return self.description

    class Meta:
        proxy = True


class Tle(models.Model):
    """Model for TLEs."""
    tle0 = models.CharField(
        max_length=69, blank=True, validators=[MinLengthValidator(1),
                                               MaxLengthValidator(69)]
    )
    tle1 = models.CharField(
        max_length=69, blank=True, validators=[MinLengthValidator(69),
                                               MaxLengthValidator(69)]
    )
    tle2 = models.CharField(
        max_length=69, blank=True, validators=[MinLengthValidator(69),
                                               MaxLengthValidator(69)]
    )
    tle_source = models.CharField(max_length=300, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True)
    satellite = models.ForeignKey(
        Satellite, null=True, blank=True, related_name='tle_sets', on_delete=models.SET_NULL
    )
    url = models.URLField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-updated']
        indexes = [
            models.Index(fields=['-updated']),
        ]
        permissions = [('access_all_tles', 'Access all TLEs')]

    def __str__(self):
        return '{:d} - {:s}'.format(self.id, self.tle0)

    @property
    def str_array(self):
        """Return TLE in string array format"""
        # tle fields are unicode, pyephem and others expect python strings
        return [str(self.tle0), str(self.tle1), str(self.tle2)]


class LatestTleSet(models.Model):
    """LatestTleSet holds the latest entry of a Satellite Tle Set"""
    satellite = models.OneToOneField(
        Satellite, related_name='latest_tle_set', on_delete=models.CASCADE
    )
    latest = models.ForeignKey(Tle, null=True, related_name='latest', on_delete=models.SET_NULL)
    latest_distributable = models.ForeignKey(
        Tle, null=True, related_name='latest_distributable', on_delete=models.SET_NULL
    )
    last_modified = models.DateTimeField(auto_now=True)

    class CacheOptions:  # pylint: disable=C0115,R0903
        cache_purge_keys = ["latesttleset_with_perms", "latesttleset_without_perms"]


class Telemetry(models.Model):
    """Model for satellite telemetry decoders."""
    satellite = models.ForeignKey(
        Satellite, null=True, related_name='telemetries', on_delete=models.SET_NULL
    )
    name = models.CharField(max_length=45)
    decoder = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['satellite__satellite_entry__norad_cat_id']
        verbose_name_plural = 'Telemetries'

    def __str__(self):
        return self.name

    def get_kaitai_fields(self):
        """Return an empty-value dict of fields for this kaitai.io struct
        Beware the overuse of "decoder" in satnogsdecoders and "decoder" the
        field above in this Telemetry model"""
        results = {}
        try:
            decoder_class = getattr(satnogsdecoders.decoder, self.decoder.capitalize())
            results = satnogsdecoders.decoder.get_fields(decoder_class, empty=True)
        except AttributeError:
            pass
        return results


class DemodData(models.Model):
    """Model for satellite for observation data."""
    satellite = models.ForeignKey(
        Satellite, null=True, related_name='telemetry_data', on_delete=models.SET_NULL
    )
    transmitter = models.ForeignKey(
        TransmitterEntry, null=True, blank=True, on_delete=models.SET_NULL
    )
    app_source = models.CharField(
        choices=list(zip(DATA_SOURCES, DATA_SOURCES)), max_length=7, default='sids'
    )
    observation_id = models.IntegerField(blank=True, null=True)
    station_id = models.IntegerField(blank=True, null=True)
    data_id = models.PositiveIntegerField(blank=True, null=True)
    payload_frame = models.FileField(upload_to=_name_payload_frame, blank=True, null=True)
    payload_decoded = models.TextField(blank=True)
    payload_telemetry = models.ForeignKey(
        Telemetry, null=True, blank=True, on_delete=models.SET_NULL
    )
    station = models.CharField(max_length=45, default='Unknown')
    observer = models.CharField(max_length=60, blank=True)
    lat = models.FloatField(validators=[MaxValueValidator(90), MinValueValidator(-90)], default=0)
    lng = models.FloatField(
        validators=[MaxValueValidator(180), MinValueValidator(-180)], default=0
    )
    is_decoded = models.BooleanField(default=False, db_index=True)
    timestamp = models.DateTimeField(null=True, db_index=True)
    version = models.CharField(max_length=45, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return 'data-for-{0}'.format(self.satellite.satellite_identifier.sat_id)

    def display_frame(self):
        """Returns the contents of the saved frame file for this DemodData

        :returns: the contents of the saved frame file for this DemodData
        """
        try:
            with open(self.payload_frame.path, encoding='utf-8') as frame_file:
                return frame_file.read()
        except IOError as err:
            LOGGER.error(
                err, exc_info=True, extra={
                    'payload frame path': self.payload_frame.path,
                }
            )
            return None
        except ValueError:  # unlikely to happen in prod, but if an entry is made without a file
            return None


class ExportedFrameset(models.Model):
    """Model for exported frames."""
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(get_user_model(), null=True, on_delete=models.SET_NULL)
    satellite = models.ForeignKey(Satellite, null=True, on_delete=models.SET_NULL)
    exported_file = models.FileField(upload_to=_name_exported_frames, blank=True, null=True)
    start = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)


class Artifact(models.Model):
    """Model for observation artifacts."""

    artifact_file = models.FileField(upload_to='artifacts/', blank=True, null=True)

    network_obs_id = models.BigIntegerField(blank=True, null=True)

    def __str__(self):
        return 'artifact-{0}'.format(self.id)
