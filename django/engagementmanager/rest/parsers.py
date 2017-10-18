#  
# ============LICENSE_START========================================== 
# org.onap.vvp/engagementmgr
# ===================================================================
# Copyright © 2017 AT&T Intellectual Property. All rights reserved.
# ===================================================================
#
# Unless otherwise specified, all software contained herein is licensed
# under the Apache License, Version 2.0 (the “License”);
# you may not use this software except in compliance with the License.
# You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Unless otherwise specified, all documentation contained herein is licensed
# under the Creative Commons License, Attribution 4.0 Intl. (the “License”);
# you may not use this documentation except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://creativecommons.org/licenses/by/4.0/
#
# Unless required by applicable law or agreed to in writing, documentation
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ============LICENSE_END============================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from rest_framework import parsers
from bleach.sanitizer import Cleaner
from django.http.request import QueryDict


sanitizer = Cleaner(
    tags=['a', 'b', 'i', 'p', 'span', 'div'],
    attributes=['font-weight', 'href', 'style', 'bold'],
    styles=[
        'color', 'font-family', 'font-style', 'font-weight',
        'text-decoration-line',
        ],
    protocols=['http'],
    strip=True,
    )


def clean_r(obj):
    """Apply bleach.clean() to strings in the given object, recursively.

    Note that this applies clean() to keys as well as values.
    """

    # DataAndFiles objects: recurse on .data, passthrough .files
    if isinstance(obj, parsers.DataAndFiles):
        return parsers.DataAndFiles(clean_r(obj.data), obj.files)

    # QueryDict: make new empty mutable object. Update, make immutable, return.
    if isinstance(obj, QueryDict):
        new_obj = QueryDict(mutable=True, encoding=obj.encoding)
        for k, v in obj.lists():
            new_obj.setlistdefault(sanitizer.clean(k)).extend(clean_r(v))
        new_obj._mutable = False
        return new_obj

    # dict-like objects: clean keys, recursive-clean values
    if callable(getattr(obj, "items", None)):
        return obj.__class__(
            (sanitizer.clean(k), clean_r(v))
            for k, v in obj.items())

    # string-like objects: clean
    if isinstance(obj, str):
        return sanitizer.clean(obj)

    # list-like objects / iterables: recurse on all items
    if callable(getattr(obj, "__iter__", None)):
        return obj.__class__(clean_r(x) for x in obj)

    # anything else: pass through
    return obj


class XSSParserMixin(parsers.BaseParser):
    """Apply this mixin to rest_framework.parsers.BaseParser subclasses to
    cause clean_r() to be run against the parsed data.

    """
    def parse(self, stream, media_type=None, parser_context=None):
        return clean_r(
            super().parse(
                stream,
                media_type=media_type,
                parser_context=parser_context))


class XSSJSONParser(XSSParserMixin, parsers.JSONParser):
    pass


class XSSFormParser(XSSParserMixin, parsers.FormParser):
    pass


class XSSMultiPartParser(XSSParserMixin, parsers.MultiPartParser):
    pass


# There's no need to XSS-scrub FileUploadParser since its DataAndFiles.data is
# always empty.
