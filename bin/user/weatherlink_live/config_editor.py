# Copyright © 2020-2023 Michael Schantl and contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from typing import Any, Dict, Tuple, List

import weecfg
import weewx.drivers
from user.weatherlink_live.utils import to_list

_MAPPER_TEMPLATE_LIST = List[Tuple[str, List[str]]]

_MAPPINGS_TEMPLATES: _MAPPER_TEMPLATE_LIST = [
    (
        "Vantage Pro2 or Vantage Vue",
        ['th:1', 'rain:1', 'wind:1', 'windchill:1', 'thw:1:appTemp', 'th_indoor', "baro", 'battery:1:outTemp:rain:wind']
    ),
    (
        "Vantage Pro2 Plus",
        ['th:1', 'rain:1', 'wind:1', 'uv:1', 'solar:1', 'windchill:1', 'thw:1', 'thsw:1:appTemp', 'th_indoor', 'baro',
         'battery:1:outTemp:rain:wind:uv']
    ),
    (
        "Vantage Pro2 Plus with additional anemometer transmitter",
        ['th:1', 'rain:1', 'wind:2', 'uv:1', 'solar:1', 'windchill:1', 'thw:1', 'thsw:1:appTemp', 'th_indoor', 'baro',
         'battery:1:outTemp:rain:uv', 'battery:2:wind']
    ),
    (
        "Vantage Pro2 Plus with soil/leaf station",
        ['th:1', 'rain:1', 'wind:1', 'uv:1', 'solar:1', 'windchill:1', 'thw:1', 'thsw:1:appTemp', 'soil_temp:2:1',
         'soil_temp:2:2', 'soil_temp:2:3', 'soil_temp:2:4', 'soil_moist:2:1', 'soil_moist:2:2', 'soil_moist:2:3',
         'soil_moist:2:4', 'leaf_wet:2:1', 'leaf_wet:2:2', 'th_indoor', 'baro', 'battery:1:outTemp:rain:wind:uv',
         'battery:2:tx']
    ),
]

_URL_HELP_INSTALLATION = "https://github.com/michael-slx/weewx-weatherlink-live/blob/develop/docs/installation.md"
_URL_HELP_MAPPING_CONFIGURATION = "https://github.com/michael-slx/weewx-weatherlink-live/blob/develop/docs/configuration.md#defining-mappings"


def _prompt_host(old_host: str | None) -> str:
    print("\n")
    print("Specify the IP address (e.g. 192.168.1.123) or hostname (e.g. weatherlinklive")
    print("or weatherlinklive.localdomain) of the WeatherLink LIVE.)")
    print("The device must be reachable via HTTP (TCP port 80) and must be on the same")
    print("subnet/VLAN. If this is not the case, 2.5-second live updates will not work")
    print("(sent as broadcast packets on UDP port 22222).")
    return weecfg.prompt_with_options("IP/Hostname", old_host)


def _prompt_mappings() -> List[str]:
    print("\n")
    print("""WeeWX uses a configurable but fixed database schema to store the recorded data.
WeatherLink LIVE however allows an arbitrary combination of transmitter types
and sensors. There is no way to automatically determine the sensors connected.

Because of this, the mappings from WeatherLink LIVE sensors to WeeWX have to be
manually configured. The following interactive menu allows you to choose from
templates. You can customize them manually later.

For more details on mappings and how to manually edit them, see the online
documentation:
%s""" % _URL_HELP_MAPPING_CONFIGURATION)

    _print_mapping_templates_menu()
    template_no = weecfg.prompt_with_options("Use template (blank for none)", "",
                                             [*[str(i) for i in range(0, len(_MAPPINGS_TEMPLATES))], ""])
    if len(template_no) <= 0:
        return []

    template_idx = int(template_no)
    return _MAPPINGS_TEMPLATES[template_idx][1]


def _print_mapping_templates_menu():
    print("")
    print("Mapping templates:")
    for i, (title, _) in enumerate(_MAPPINGS_TEMPLATES):
        print("%3s: %s" % (str(i), title))


def _print_mappings_exists() -> None:
    print("\n")
    print("""There are already some configured mappings. You can customize them manually
by editing the WeeWX configuration file.

For more details on mappings and how to manually edit them, see the online
documentation:
%s""" % _URL_HELP_MAPPING_CONFIGURATION)


def _print_mapping_table_info():
    print("\n")
    print("""You can display all mappings by running the following command:
$ wee_device --print-mapping""")


def _print_schema_info():
    print("\n")
    print("""In order to utilize the full potential of your WeatherLink LIVE, you should use
the database schema included with this driver.

See the installation manual for detailed instructions:
%s""" % _URL_HELP_INSTALLATION)


class WeatherlinkLiveConfEditor(weewx.drivers.AbstractConfEditor):
    def __init__(self):
        self.existing_options = dict()

    @property
    def default_stanza(self):
        return """
#   This section configures the WeatherLink Live driver

[WeatherLinkLive]
    # Driver module
    driver = user.weatherlink_live

    # Host name or IP address of WeatherLink Live
    host = weatherlinklive

    # Mapping of transmitter ids to WeeWX records
    mapping = ,

    # Whether to log successful operations. Overrides top-level setting.
    #log_success = False

    # Whether to log unsuccessful operations. Overrides top-level setting.
    #log_failure = True
"""

    def prompt_for_settings(self) -> Dict[str, Any]:
        settings = self.existing_options

        old_host = settings.get('host', None)
        old_host = old_host if old_host and len(old_host) > 0 else None
        host = _prompt_host(old_host)
        settings['host'] = host

        mapping_def_cfg_list = to_list(settings.get('mapping', []))
        if len(mapping_def_cfg_list) <= 0:
            mapping_def_cfg_list = _prompt_mappings()
            settings['mapping'] = mapping_def_cfg_list
        else:
            _print_mappings_exists()

        _print_mapping_table_info()

        _print_schema_info()

        return settings

    def modify_config(self, config_dict):
        print("\n")
        print("""Configuring accumulators for custom types.""")

        config_dict.setdefault('Accumulator', {})

        config_dict['Accumulator'].setdefault('rainCount', {})
        config_dict['Accumulator']['rainCount']['extractor'] = 'sum'

        config_dict['Accumulator'].setdefault('rainSize', {})
        config_dict['Accumulator']['rainSize']['extractor'] = 'last'
