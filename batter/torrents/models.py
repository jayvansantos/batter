from __future__ import absolute_import, unicode_literals

import binascii
import collections

import bencode
from django.db import models
from django.core.urlresolvers import reverse
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible, force_bytes
from django.utils.translation import ugettext as _

from jsonfield import JSONField
from model_utils.models import TimeStampedModel
from taggit.managers import TaggableManager

from . import managers


@python_2_unicode_compatible
class Torrent(models.Model):
    announce = models.TextField(help_text="The announce URL of the tracker.")
    announce_list = JSONField(blank=True, null=True)
    creation_date = models.PositiveIntegerField(blank=True, null=True,
        help_text=_("Torrent creation time in UNIX epoch format."))
    comment = models.TextField(blank=True, null=True,
        help_text=_("Free-form textual comment of the torrent author."))
    created_by = models.TextField(blank=True, null=True,
        help_text=_("Name and version of the program used to create the "
                    "torrent."))
    encoding = models.TextField(blank=True, null=True,
        help_text=_("Encoding used to generate the pieces part of the info "
                    "dictionary in the torrent metadata"))
    piece_length = models.PositiveIntegerField(blank=True, null=True,
        help_text=_("Number of bytes in each piece"))
    pieces = models.TextField(unique=True,
        help_text=_("A concatenation of all 20-byte SHA1 hash values of the "
                    "torrent's pieces"))
    is_private = models.BooleanField(
        help_text=_("Whether or not the client may obtain peer data from "
                    "other sources (PEX, DHT)."))
    name = models.TextField(
        help_text=_("The suggested name of the torrent file, if single-file "
                    "torrent, otherwise, the suggest name of the directory "
                    "in which to put the files"))
    length = models.PositiveIntegerField(blank=True, null=True,
        help_text=_("Length of the file contents in bytes, missing for "
                    "multi-file torrents."))
    md5sum = models.CharField(blank=True, null=True, max_length=32,
        help_text=_("MD5 hash of the file contents (single-file torrent only)."))
    files = JSONField(blank=True, null=True,
        help_text=_("A list of {name, length, md5sum} dicts corresponding to "
                    "the files tracked by the torrent"))

    @classmethod
    def from_torrent_file(cls, torrent_file, *args, **kwargs):
        torrent_dict = bencode.bdecode(torrent_file.read())
        return cls.from_torrent_dict(torrent_dict, *args, **kwargs)

    @classmethod
    def from_torrent_dict(cls, torrent_dict, *args, **kwargs):
        info_dict = torrent_dict[b'info']
        torrent = cls()
        torrent.announce = torrent_dict[b'announce']
        torrent.announce_list = torrent_dict.get(b'announce-list')
        torrent.creation_date = torrent_dict.get(b'creation date')
        torrent.comment = torrent_dict.get(b'comment')
        torrent.created_by = torrent_dict.get(b'created by')
        torrent.encoding = torrent_dict.get(b'encoding')
        torrent.piece_length = info_dict.get(b'piece length')
        torrent.pieces = binascii.hexlify(info_dict.get(b'pieces'))
        torrent.private = info_dict.get(b'private', 0) == 1
        torrent.name = info_dict.get(b'name')
        torrent.length = info_dict.get(b'length')
        torrent.md5sum = info_dict.get(b'md5sum')
        torrent.files = info_dict.get(b'files')
        return torrent

    def get_absolute_url(self):
        return reverse('torrents_view', args=[str(self.id)])

    @property
    def is_single_file(self):
        return self.files is None or len(self.files) > 1
    
    def to_bencoded_string(self, *args, **kwargs):
        def drop_empty(d):
            """Recursively drops falsy values from a dict and coerces
            everything else to :class:`bytes`."""
            if isinstance(d, dict):
                return dict((k, drop_empty(v)) for k, v in d.items() if v)
            else:
                return force_bytes(d)
            
        torrent = {
            b'announce': self.announce,
            b'announce-list': self.announce_list,
            b'creation date': self.creation_date,
            b'comment': self.comment,
            b'created by': self.created_by,
            b'encoding': self.encoding,
        }

        torrent[b'info'] = info_dict = {
            b'piece length': self.piece_length,
            b'pieces': binascii.unhexlify(self.pieces),
            b'private': int(self.is_private),
            b'name': self.name
        }
        if self.is_single_file:
            info_dict[b'length'] = self.length
            info_dict[b'md5sum'] = self.md5sum
        else:
            info_dict[b'files'] = self.files

        return bencode.bencode(drop_empty(torrent))

    def __str__(self):
        return self.name


class InheritingModel(models.Model):
    _child_name = models.CharField(max_length=100, editable=False)

    objects = managers.InheritingManager()
    base_objects = models.Manager()

    def save(self, *args, **kwargs):
        # NB: based on http://djangosnippets.org/snippets/1037/
        self._child_name = self.get_child_name()
        super(InheritingModel, self).save(*args, **kwargs)

    def get_child_name(self):
        if type(self) is self.get_parent_model():
            return self._child_name
        return self.get_parent_link().related_query_name()

    def get_child_object(self):
        return getattr(self, self.get_child_name())

    def get_parent_link(self):
        return self._meta.parents[self.get_parent_model()]

    def get_parent_model(self):  # pragma: no cover
        # this method is excluded from coverage purely because it should never
        # be run. at all. it's only here so you know you have to override it.
        raise NotImplementedError

    def get_parent_object(self):
        return getattr(self, self.get_parent_link().name)

    class Meta:
        abstract = True


class Upload(InheritingModel, TimeStampedModel):
    torrent = models.OneToOneField(
        Torrent,
        related_name='upload',
        null=False
    )
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    parent = models.ForeignKey(
        'TorrentGroup',
        null=False,
        related_name='uploads'
    )

    def get_parent_model(self):
        return Upload


class TorrentGroup(InheritingModel, TimeStampedModel):
    tags = TaggableManager()

    def get_parent_model(self):
        return TorrentGroup


def convert(data):
    """ Converts unicode (or a dict/Mapping/Iterable containing unicode
    strings) to str. """
    if isinstance(data, basestring):
        return str(data)
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data
