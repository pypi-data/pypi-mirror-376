"""
agnomux2 - Lightweight Universal API Router

Route requests to any API through configuration instead of hardcoded clients.
Plug in your own transports and parsers as needed. Supports sync/async and streaming.
Bring-your-own transports and parsers.

Example:
    router = Router()
    router.add_endpoint('weather', { 'transport': 'http', 'parser': 'json' })
    response = router.route('weather', city="London")

#### Copyright (c) 2025 gauravkg32
#### Part of the Agnosweaver™ project suite
####
#### Licensed under the PolyForm Noncommercial License 1.0.0
#### See the LICENSE file for details.

Project Homepage: https://github.com/agnosweaver/agnomux2
"""


from .agnomux2 import Router, Response, StreamChunk, RawResponse, AgnomuxError
from .agnomux2 import BaseTransport, BaseParser, BaseTemplateEngine
from .agnomux2 import Registry, TransportRegistry, ParserRegistry, TemplateRegistry

__version__ = "0.0.1a0"
__all__ = [
    'Router', 'Response', 'StreamChunk', 'RawResponse', 'AgnomuxError',
    'BaseTransport', 'BaseParser', 'BaseTemplateEngine',
    'Registry', 'TransportRegistry', 'ParserRegistry', 'TemplateRegistry'
]