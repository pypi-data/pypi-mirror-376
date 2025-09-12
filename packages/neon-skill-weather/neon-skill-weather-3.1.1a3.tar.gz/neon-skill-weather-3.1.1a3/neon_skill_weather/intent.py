# Copyright 2021, Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parse the intent into data used by the weather skill."""

import pytz
from ovos_config.locale import get_default_tz
from datetime import datetime, timedelta
from neon_utils.location_utils import get_coordinates, get_location, get_timezone
from ovos_utils import LOG

from .util import (
    get_utterance_datetime,
    # get_geolocation,
    get_tz_info,
    LocationNotFoundError,
)
from .weather import CURRENT


class WeatherIntent:
    _geolocation = None
    _intent_datetime = None
    _location_datetime = None
    _translator = None

    def __init__(self, message, language):
        """Constructor

        :param message: Intent data from the message bus
        :param language: The configured language of the device
        """
        self.utterance = message.data["utterance"]
        self.location = message.data.get("location")
        self.language = language
        self.unit = message.data.get("unit")
        self.timeframe = CURRENT
        self._location = None

    def _get_location(self):
        lat, lng = get_coordinates({"city": self.location})
        # TODO: `get_location` should support non-English requests in the future
        city, county, state, country = get_location(lat, lng)
        if not city and county:
            city = f'{county} county'
        if not city:
            raise LocationNotFoundError(f"{self.location} could not be resolved")
        self._location = {'city': city,
                          'region': state,
                          'country': country,
                          'timezone': str(pytz.timezone(get_timezone(lat, lng)[0])),
                          'latitude': lat,
                          'longitude': lng
                          }
        if self.language.split('-')[0] != 'en':
            LOG.info(f"Translating location names from `en` to "
                     f"`{self.language}`")
            self._location = self._translator.translate_dict(
                self._location, self.language.split('-')[0], 'en')

            # TODO: Better patch than this
            if city == "Dusseldorf" and self.language.split('-')[0] == 'de':
                self._location['city'] = 'Düsseldorf'

        LOG.debug(f"location={self._location}")
        return self._location

    @property
    def geolocation(self):
        """Lookup the intent location using the Selene API.

        The Selene geolocation API assumes the location of a city is being
        requested.  If the user asks "What is the weather in Russia"
        an error will be raised.
        """
        if self._geolocation is None:
            if self.location is None:
                self._geolocation = dict()
            else:
                self._geolocation = self._get_location()
                if not self._geolocation.get("city"):
                    raise LocationNotFoundError(self.location + " is not a city")

        return self._geolocation

    @property
    def intent_datetime(self):
        """Use the configured timezone and the utterance to know the intended time.

        If a relative date or relative time is supplied in the utterance, use a
        datetime object representing the request.  Otherwise, use the timezone
        configured by the device.
        """
        if self._intent_datetime is None:
            utterance_datetime = get_utterance_datetime(
                self.utterance,
                timezone=self.geolocation.get("timezone"),
                language=self.language,
            )
            if utterance_datetime is not None:
                delta = utterance_datetime - self.location_datetime
                if int(delta / timedelta(days=1)) > 7:
                    raise ValueError("Weather forecasts only supported up to 7 days")
                if utterance_datetime.date() < self.location_datetime.date():
                    raise ValueError("Historical weather is not supported")
                self._intent_datetime = utterance_datetime
            else:
                self._intent_datetime = self.location_datetime

        return self._intent_datetime

    @property
    def location_datetime(self):
        """Determine the current date and time for the request.

        If a location is specified in the request, use the timezone for that
        location, otherwise, use the timezone configured on the device.
        """
        if self._location_datetime is None:
            if self.location is None:
                self._location_datetime = datetime.now(get_default_tz())
            else:
                tz_info = get_tz_info(self.geolocation["timezone"])
                self._location_datetime = datetime.now(tz_info)

        return self._location_datetime
