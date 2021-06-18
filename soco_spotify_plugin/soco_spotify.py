#!/usr/bin/env python3
# coding: utf-8

"""Spotify plugin for Sonos."""

import re
from xml.sax.saxutils import escape
from soco.plugins import SoCoPlugin
from soco.music_services import MusicService
from soco.music_services.accounts import Account
from soco.data_structures import (DidlResource, DidlAudioItem, DidlAlbum,
                                  to_didl_string, DidlPlaylistContainer)
from soco.data_structures_entry import from_didl_string
from soco.exceptions import MusicServiceException
from spotipy import *
from spotipy.oauth2 import SpotifyOAuth


spotify_services = {
    "global": 2311,
    "us": 3079,
}


spotify_sonos = {
    "album": {
        "prefix": "x-rincon-cpcontainer:1004206c",
        "key": "1004206c",
        "class": "object.container.album.musicAlbum",
    },
    "track": {
        "prefix": "",
        "key": "00032020",
        "class": "object.item.audioItem.musicTrack",
    },
    "playlist": {
        "prefix": "x-rincon-cpcontainer:1006206c",
        "key": "1006206c",
        "class": "object.container.playlistContainer",
    },
}


class SpotifySocoPlugin(SoCoPlugin):
    def __init__(self, soco, spotify_service, spotify_scope,
                 spotify_client_id, spotify_client_secret, spotify_redirect_uri):
        super(SpotifySocoPlugin, self).__init__(soco)

        if spotify_service not in spotify_services:
            raise MusicServiceException("Unknown spotify service: '%s'" % spotify_service)
        self.spotify_service = spotify_services[spotify_service]

        self.sp = Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                                             client_secret=spotify_client_secret,
                                                             redirect_uri=spotify_redirect_uri,
                                                             scope=spotify_scope))


    @property
    def name(self):
        return 'Spotify'


    def get_uri(self, spotify_title, spotify_id):
        """Get URI for spotify."""
        match = re.search(r"spotify.*[:/](album|track|playlist)[:/](\w+)", spotify_id)
        if not match:
            return False
        spotify_type = match.group(1)
        encoded_uri = "spotify%3a" + match.group(1) + "%3a" + match.group(2)
        enqueue_uri = spotify_sonos[spotify_type]["prefix"] + encoded_uri

        metadata_template = ('<DIDL-Lite xmlns:dc="http://purl.org/dc/elements'
                             '/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata'
                             '-1-0/upnp/" xmlns:r="urn:schemas-rinconnetworks-'
                             'com:metadata-1-0/" xmlns="urn:schemas-upnp-org:m'
                             'etadata-1-0/DIDL-Lite/"><item id="{item_id}" par'
                             'entID="R:0/0" restricted="true"><dc:title>{item_'
                             'title}</dc:title><upnp:class>{item_class}</upnp:'
                             'class><desc id="cdudn" nameSpace="urn:schemas-ri'
                             'nconnetworks-com:metadata-1-0/">SA_RINCON{sn}_X_'
                             '#Svc{sn}-0-Token</desc></item></DIDL-Lite>')

        metadata = metadata_template.format(
            item_title=escape(spotify_title),
            item_id=spotify_sonos[spotify_type]["key"] + encoded_uri,
            item_class=spotify_sonos[spotify_type]["class"],
            sn=self.spotify_service,
        )
        return [
            ("InstanceID", 0),
            ("EnqueuedURI", enqueue_uri),
            ("EnqueuedURIMetaData", metadata),
            ("DesiredFirstTrackNumberEnqueued", 0),
            ("EnqueueAsNext", 0),
        ]
