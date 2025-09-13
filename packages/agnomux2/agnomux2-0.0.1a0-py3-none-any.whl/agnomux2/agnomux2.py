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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Dict, Optional, Iterator, AsyncIterator


# ============================================================================
# Core Data Structures and Exceptions
# ============================================================================


@dataclass
class Response:
    """Universal response container - works with any data type."""
    content: Any  # Could be str, bytes, dict, custom object, anything
    endpoint_name: str
    content_type: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass  
class StreamChunk:
    """Universal stream chunk - works with any streaming data."""
    content: Any  # Could be str, bytes, dict, custom object, anything
    endpoint_name: str          # In case you are wondering why the same field names are used twice
    content_type: str           # It's because python's weird dataclass inheritance makes
    timestamp: str              # DRY impossible and not worth the cost of complexity, so much that WET is preferable
    metadata: Optional[Dict[str, Any]] = None
    is_final: bool = False


class RawResponse:
    """Raw transport response before parsing."""
    def __init__(self, data: Any, headers: Optional[Dict] = None, status: Optional[Any] = None):
        self.data = data
        self.headers = headers or {}
        self.status = status


class AgnomuxError(Exception):
    """Base exception for Agnomux-related errors."""
    pass


# ============================================================================
# Abstract Base Classes
# ============================================================================

class BaseTransport(ABC):
    """User-extensible transport interface."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def send(self, data: Any, **kwargs) -> RawResponse:
        """Send data, return raw response."""
        pass
    
    @abstractmethod  
    async def asend(self, data: Any, **kwargs) -> RawResponse:
        """Async send data, return raw response."""
        pass
    
    def send_stream(self, data: Any, **kwargs) -> Iterator[RawResponse]:
        """Optional streaming support."""
        raise NotImplementedError("Streaming not supported by this transport")
    
    async def asend_stream(self, data: Any, **kwargs) -> AsyncIterator[RawResponse]:
        """Optional async streaming support."""
        raise NotImplementedError("Async streaming not supported by this transport")


class BaseParser(ABC):
    """User-extensible parser interface."""
    
    @abstractmethod
    def parse_request(self, data: Any, template: Dict[str, Any]) -> Any:
        """Build request from data using template."""
        pass
    
    @abstractmethod  
    def parse_response(self, raw_response: RawResponse) -> Any:
        """Parse raw response into structured data."""
        pass
    
    def get_content_type(self, raw_response: RawResponse) -> str:
        """Extract content type from raw response."""
        return raw_response.headers.get('content-type', 'unknown')
    
    def parse_stream_chunk(self, raw_chunk: RawResponse) -> Optional[Any]:
        """Parse one transport chunk into zero/one item (or a list for wrappers to split)."""
        raise NotImplementedError("Parser does not support streaming parsing")


class BaseTemplateEngine(ABC):
    """User-extensible template engine interface."""
    
    @abstractmethod
    def render_template(self, template: Any, variables: Dict[str, Any]) -> Any:
        """Render template with variables."""
        pass


# ============================================================================
# Registry System (The Magic)
# ============================================================================

class Registry:
    """Generic registry for user extensions."""
    
    def __init__(self):
        self._items = {}
    
    def register(self, name: str, item: Any):
        """Register an item by name."""
        self._items[name] = item
    
    def get(self, name: str) -> Any:
        """Get registered item by name."""
        if name not in self._items:
            raise AgnomuxError(f"'{name}' not found in registry. Available: {list(self._items.keys())}")
        return self._items[name]
    
    def list_available(self) -> list:
        """List all registered items."""
        return list(self._items.keys())


# Global registries
TransportRegistry = Registry()
ParserRegistry = Registry()
TemplateRegistry = Registry()


# ============================================================================
# Core Router (The Heart)
# ============================================================================

class Router:
    """Configuration-driven API router. This is the main interface. Not responsible for error handling.
    Note: Router does not handle errors — transport/parser exceptions bubble up to callers.
    """
    
    def __init__(self, transport_registry=TransportRegistry,
             parser_registry=ParserRegistry,
             template_registry=TemplateRegistry):
        self.transport_registry = transport_registry
        self.parser_registry = parser_registry
        self.template_registry = template_registry
        self.endpoints = {}
    
    def _get_config(self, endpoint, **data) -> Dict[str, Any]:
        """Hook for dynamic config resolution. Subclass Router to override behavior (default = static lookup)."""
        return self.endpoints[endpoint]

    def add_endpoint(self, name: str, config: Dict[str, Any]):
        """Add an endpoint with user configuration."""
        required_fields = ['transport', 'parser']
        for field in required_fields:
            if field not in config:
                raise AgnomuxError(f"Endpoint '{name}' missing required field: {field}")
        
        self.endpoints[name] = config

    def _apply_template(self, data: Dict[str, Any], template_engine_name: str, request_template: Any) -> tuple[Any, Optional[BaseTemplateEngine]]:
        """Hook for applying templating to request data. Returns (request_data, template_engine)."""
        template_engine_class = self.template_registry.get(template_engine_name)
        template_engine = template_engine_class()
        request_data = template_engine.render_template(request_template, data)
        return request_data, template_engine

    def _setup(self, endpoint: str, data: Dict[str, Any]) -> tuple[BaseTransport, BaseParser, Any, Dict[str, Any]]:
        """Common setup for routing. If template_engine is specified, uses templating instead of parser for request building."""
        if endpoint not in self.endpoints:
            raise AgnomuxError(f"Endpoint '{endpoint}' not found. Available: {list(self.endpoints.keys())}")
            
        config = self._get_config(endpoint, **data)
        
        # Get transport and parser
        transport_class = self.transport_registry.get(config['transport'])
        parser_class = self.parser_registry.get(config['parser'])

        transport = transport_class(config)
        parser = parser_class()

        # Build request - with or without template
        request_template = config.get('request_template', {})
        if config.get('template_engine') and request_template:
            request_data, _ = self._apply_template(data, config['template_engine'], request_template)
        else:
            request_data = parser.parse_request(data, request_template)
        
        return transport, parser, request_data, config


    def route(self, endpoint: str, **data) -> Response:
        """Route data to endpoint, return parsed response."""
        transport, parser, request_data, _ = self._setup(endpoint, data)
        # Send request
        raw_response = transport.send(request_data)
        
        # Parse response
        parsed_response = parser.parse_response(raw_response)
        content_type = parser.get_content_type(raw_response)
        
        return Response(
            content=parsed_response,
            endpoint_name=endpoint,
            content_type=content_type,
            timestamp=datetime.now(UTC).isoformat(),
            metadata={'raw_headers': raw_response.headers}
        )
    
    async def aroute(self, endpoint: str, **data) -> Response:
        """Async version of route."""
        transport, parser, request_data, _ = self._setup(endpoint, data)
        raw_response = await transport.asend(request_data)
        parsed_response = parser.parse_response(raw_response)
        content_type = parser.get_content_type(raw_response)
        
        return Response(
            content=parsed_response,
            endpoint_name=endpoint,
            content_type=content_type,
            timestamp=datetime.now(UTC).isoformat(),
            metadata={'raw_headers': raw_response.headers}
        )
    
    def route_stream(self, endpoint: str, **data) -> Iterator[StreamChunk]:
        """Stream data from endpoint."""
        transport, parser, request_data, _ = self._setup(endpoint, data)
        for raw_chunk in transport.send_stream(request_data):
            parsed_chunk = parser.parse_stream_chunk(raw_chunk)
            content_type = parser.get_content_type(raw_chunk)
            
            yield StreamChunk(
                content=parsed_chunk,
                endpoint_name=endpoint,
                content_type=content_type,
                timestamp=datetime.now(UTC).isoformat(),
                is_final=False
            )
    
    async def aroute_stream(self, endpoint: str, **data) -> AsyncIterator[StreamChunk]:
        """Async stream data from endpoint."""
        transport, parser, request_data, _ = self._setup(endpoint, data)
        async for raw_chunk in transport.asend_stream(request_data):
            parsed_chunk = parser.parse_stream_chunk(raw_chunk)
            content_type = parser.get_content_type(raw_chunk)
            
            yield StreamChunk(
                content=parsed_chunk,
                endpoint_name=endpoint,
                content_type=content_type,
                timestamp=datetime.now(UTC).isoformat(),
                is_final=False
            )


# ============================================================================
# The End
# ============================================================================