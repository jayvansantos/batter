from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import force_text, python_2_unicode_compatible
from django.utils.translation import ugettext as _

from django_countries import CountryField
from model_utils.models import TimeStampedModel
from taggit.managers import TaggableManager

from torrents.models import Upload, UploadGroup, DescendingModel


FORMAT_TYPES = (
    ('mp3', 'MP3'),
    ('flac', 'FLAC'),
    ('aac', 'AAC'),
    ('ac3', 'AC3'),
    ('dts', 'DTS'),
)

BITRATE_TYPES = (
    ('192', '192'),
    ('apsvbr', 'APS (VBR)'),
    ('v2vbr', 'V2 (VBR)'),
    ('v1vbr', 'V1 (VBR)'),
    ('256', '256'),
    ('apxvbr', 'APX (VBR)'),
    ('v0vbr', 'V0 (VBR)'),
    ('320', '320'),
    ('lossless', _('Lossless')),
    ('24bitlossless', _('24Bit Lossless')),
    ('v8vbr', 'V8 (VBR)'),
    ('other', _('Other')),

)

MEDIA_TYPES = (
    ('cd', 'CD'),
    ('dvd', 'DVD'),
    ('vinyl', _('Vinyl')),
    ('soundboard', _('Soundboard')),
    ('sacd', 'SACD'),
    ('dat', 'DAT'),
    ('cassette', _('Cassette')),
    ('web', 'WEB'),
    ('bluray', 'Blu-Ray'),
)

RELEASE_TYPES = (
    ('album', _('Album')),
    ('soundtrack', _('Soundtrack')),
    ('ep', _('EP')),
    ('anthology', _('Anthology')),
    ('compilation', _('Compilation')),
    ('djmix', _('DJ Mix')),
    ('single', _('Single')),
    ('livealbum', _('Live Album')),
    ('remix', _('Remix')),
    ('bootleg', _('Bootleg')),
    ('interview', _('Interview')),
    ('mixtape', _('Mixtape')),
    ('unknown', _('Unknown'))
)


@python_2_unicode_compatible
class MusicUpload(Upload):
    release = models.ForeignKey('Release')
    release_format = models.TextField(choices=FORMAT_TYPES)
    bitrate = models.TextField(choices=BITRATE_TYPES)
    media = models.TextField(choices=MEDIA_TYPES)
    logfile = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('Release', related_name='_children')

    class Meta:
        verbose_name = _('music upload')
        verbose_name_plural = _('music uploads')

    def __str__(self):
        return "{0} / {1} / {2}".format(
            self.master.release,
            force_text(self.format),
            force_text(self.bitrate)
        )


@python_2_unicode_compatible
class Artist(TimeStampedModel):
    name = models.TextField()
    sort_name = models.SlugField()
    discogs_id = models.PositiveIntegerField()
    country = CountryField()
    gender = models.TextField()
    disambiguation = models.TextField(blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    birthdate = models.DateField(blank=True, null=True)
    deathdate = models.DateField(blank=True, null=True)
    tags = TaggableManager()
    related_artists = models.ManyToManyField(
        'self',
        related_name="artist_related_artists",
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('artist')
        verbose_name_plural = _('artists')

    def __str__(self):
        return force_text(self.name)


@python_2_unicode_compatible
class ArtistAlias(models.Model):
    alias = models.TextField()
    artist = models.ForeignKey('Artist')

    class Meta:
        verbose_name = _('artist alias')
        verbose_name_plural = _('artist aliases')

    def __str__(self):
        return force_text(self.alias)


@python_2_unicode_compatible
class Release(DescendingModel, TimeStampedModel):
    name = models.TextField()
    discogs_id = models.PositiveIntegerField()
    artist_credit = models.ManyToManyField('Artist')
    comment = models.TextField()
    label = models.ForeignKey('Label')
    release_type = models.TextField(choices=RELEASE_TYPES)
    country = CountryField()
    date = models.DateField()
    parent = models.ForeignKey('Master', related_name='_children')

    class Meta:
        verbose_name = _('release')
        verbose_name_plural = _('releases')

    def get_child_model(self):
        return MusicUpload

    def __str__(self):
        return force_text(self.name)


@python_2_unicode_compatible
class Master(UploadGroup):
    name = models.TextField()
    discogs_id = models.PositiveIntegerField()
    artist_credit = models.ManyToManyField('Artist')
    comment = models.TextField()

    class Meta:
        verbose_name = _('master')
        verbose_name_plural = _('masters')

    def get_child_model(self):
        return Release

    def __str__(self):
        return force_text(self.name)


@python_2_unicode_compatible
class Label(TimeStampedModel):
    name = models.TextField()
    parent_label = models.ForeignKey('self', blank=True, null=True)

    class Meta:
        verbose_name = _('master')
        verbose_name_plural = _('masters')

    def is_vanity(self):
        return bool(self.parent_label)

    def __str__(self):
        return force_text(self.name)
