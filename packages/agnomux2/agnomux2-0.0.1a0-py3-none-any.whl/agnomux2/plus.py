"""
agnomux2.plus - For Batteries-Included behavior and advanced features
Comes with PlusRouter, built-in transports (HTTP, WebSocket),
parsers (JSON, Plaintext, Binary, Custom), Simple templating, and auth registry.
Includes enchanced error handling and a minimal CLI for testing.

#### Copyright (c) 2025 gauravkg32
#### Part of the Agnosweaver™ project suite
####
#### Licensed under the PolyForm Noncommercial License 1.0.0
#### See the LICENSE file for details.

Project Homepage: https://github.com/agnosweaver/agnomux2
"""


import re
import json
from typing import Any, Dict, Generator, AsyncGenerator, Optional


from .agnomux2 import (Router as BaseRouter, BaseParser, BaseTransport, BaseTemplateEngine,
                       TransportRegistry, ParserRegistry, TemplateRegistry,
                       AgnomuxError, RawResponse, Registry)


# ============================================================================
# Plus Exceptions
# ============================================================================


class TransportError(AgnomuxError):
    """Raised when a transport fails (network, timeout, connection, etc.)"""
    pass

class ParserError(AgnomuxError):
    """Raised when a parser fails to parse a response or stream chunk"""
    pass

class AuthError(AgnomuxError):
    """Raised when authentication fails"""
    pass

class TemplateError(AgnomuxError):
    """Raised when a template fails to render"""
    pass


# ============================================================================
# Transport Implementations
# ============================================================================


class HTTPTransport(BaseTransport):
    """HTTP transport implementation"""

    def __init__(self, config: dict):
        self.endpoint = config.get("url")
        self.method = config.get("method", "POST")
        self.headers = config.get("headers", {})

    def send(self, request_data: Any, **kwargs) -> RawResponse:
        """Sync HTTP request"""
        import requests
        try:
            response = requests.request(
                method=self.method,
                url=self.endpoint,
                headers=self.headers,
                json=request_data,
                timeout=kwargs.get("timeout", 30),
            )
            response.raise_for_status()
            return RawResponse(
                data=response.text,
                headers=dict(response.headers),
                status=response.status_code,
            )
        except requests.RequestException as e:
            raise TransportError("HTTP request failed") from e

    async def asend(self, request_data: Any, **kwargs) -> RawResponse:
        """Async HTTP request"""
        import aiohttp
        try:
            timeout = aiohttp.ClientTimeout(total=kwargs.get("timeout", 30))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=self.method,
                    url=self.endpoint,
                    headers=self.headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()
                    return RawResponse(
                        data=await response.text(),
                        headers=dict(response.headers),
                        status=response.status,
                    )
        except (aiohttp.ClientError, Exception) as e:
            raise TransportError("HTTP request failed") from e

    def send_stream(self, request_data: Any, **kwargs) -> Generator[RawResponse, None, None]:
        """Sync streaming HTTP request"""
        import requests
        try:
            with requests.request(
                method=self.method,
                url=self.endpoint,
                headers=self.headers,
                json=request_data,
                timeout=kwargs.get("timeout", 30),
                stream=True,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines(decode_unicode=True):
                    if line:
                        yield RawResponse(
                            data=line,
                            headers=dict(response.headers),
                            status=response.status_code,
                        )
        except requests.RequestException as e:
            raise TransportError("HTTP streaming request failed") from e

    async def asend_stream(self, request_data: Any, **kwargs) -> AsyncGenerator[RawResponse, None]:
        """Async streaming HTTP request"""
        import aiohttp
        try:
            timeout = aiohttp.ClientTimeout(total=kwargs.get("timeout", 30))
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.request(
                    method=self.method,
                    url=self.endpoint,
                    headers=self.headers,
                    json=request_data,
                ) as response:
                    response.raise_for_status()
                    async for line in response.content:
                        if line:
                            yield RawResponse(
                                data=line.decode("utf-8"),
                                headers=dict(response.headers),
                                status=response.status,
                            )
        except (aiohttp.ClientError, Exception) as e:
            raise TransportError("HTTP streaming request failed") from e


class WebSocketTransport(BaseTransport):
    """WebSocket transport implementation"""

    def __init__(self, config: dict):
        self.endpoint = config.get("url")
        self.headers = config.get("headers", {})        # optional
        self.subprotocols = config.get("subprotocols")  # optional (list of strings)

    def send(self, request_data: Any, **kwargs) -> RawResponse:
        """Sync WebSocket request - not typically used"""
        raise NotImplementedError("Synchronous WebSocket not supported")

    async def asend(self, request_data: Any, **kwargs) -> RawResponse:
        """Async WebSocket request"""
        import websockets
        try:
            async with websockets.connect(
                self.endpoint,
                extra_headers=self.headers,
                subprotocols=self.subprotocols,
            ) as websocket:
                await websocket.send(json.dumps(request_data))
                response = await websocket.recv()
                return RawResponse(
                    data=response,
                    headers={},  # WebSockets don’t expose headers after handshake
                    status=None,
                )
        except Exception as e:
            raise TransportError("WebSocket request failed") from e

    def send_stream(self, request_data: Any, **kwargs) -> Generator[RawResponse, None, None]:
        """Sync WebSocket streaming - not typically used"""
        raise NotImplementedError("Synchronous WebSocket streaming not supported")

    async def asend_stream(self, request_data: Any, **kwargs) -> AsyncGenerator[RawResponse, None]:
        """Async WebSocket streaming"""
        import websockets
        try:
            async with websockets.connect(
                self.endpoint,
                extra_headers=self.headers,
                subprotocols=self.subprotocols,
            ) as websocket:
                await websocket.send(json.dumps(request_data))
                while True:
                    try:
                        response = await websocket.recv()
                        yield RawResponse(
                            data=response,
                            headers={},
                            status=None,
                        )
                    except websockets.exceptions.ConnectionClosed:
                        break
        except Exception as e:
            raise TransportError("WebSocket streaming request failed") from e


# ============================================================================
# Response Parsers
# ============================================================================


class JSONResponseParser(BaseParser):
    """Parser for JSON responses"""

    def parse_request(self, data: Any, template: dict) -> Any:
        """Simply merge input data with template"""
        # JSON requests are usually dicts
        request = template.copy()
        request.update(data)
        return request

    def parse_response(self, raw_response: RawResponse) -> Any:
        try:
            return json.loads(raw_response.data)
        except Exception as e:
            raise ParserError(f"Failed to parse JSON response: {e}") from e

    def parse_stream_chunk(self, raw_chunk: RawResponse) -> Optional[Any]:
        try:
            return json.loads(raw_chunk.data)
        except Exception:
            # Drop invalid chunks instead of crashing
            return None

    def get_content_type(self, raw_response: RawResponse) -> str:
        return raw_response.headers.get("content-type", "application/json")


class PlainTextResponseParser(BaseParser):
    """Parser for plain text responses"""

    def parse_request(self, data: Any, template: dict) -> Any:
        # Naive implementation: just cast to string
        return str(data)

    def parse_response(self, raw_response: RawResponse) -> str:
        try:
            return str(raw_response.data)
        except Exception as e:
            raise ParserError(f"Failed to parse plain text response: {e}") from e

    def parse_stream_chunk(self, raw_chunk: RawResponse) -> Optional[str]:
        try:
            return str(raw_chunk.data)
        except Exception:
            return None

    def get_content_type(self, raw_response: RawResponse) -> str:
        return raw_response.headers.get("content-type", "text/plain")


class BinaryResponseParser(BaseParser):
    """Parser for binary responses"""

    def parse_request(self, data: Any, template: dict) -> Any:
        # Assume request data is already bytes
        if isinstance(data, bytes):
            return data
        raise ParserError("Binary request data must be bytes")

    def parse_response(self, raw_response: RawResponse) -> bytes:
        try:
            return (
                raw_response.data
                if isinstance(raw_response.data, bytes)
                else raw_response.data.encode("utf-8")
            )
        except Exception as e:
            raise ParserError(f"Failed to parse binary response: {e}") from e

    def parse_stream_chunk(self, raw_chunk: RawResponse) -> Optional[bytes]:
        try:
            return (
                raw_chunk.data
                if isinstance(raw_chunk.data, bytes)
                else raw_chunk.data.encode("utf-8")
            )
        except Exception:
            return None

    def get_content_type(self, raw_response: RawResponse) -> str:
        return raw_response.headers.get("content-type", "application/octet-stream")


class CustomResponseParser(BaseParser):
    """Parser that delegates to a user-provided callable"""

    def __init__(self, parse_fn):
        if not callable(parse_fn):
            raise ParserError("CustomResponseParser requires a callable")
        self.parse_fn = parse_fn

    def parse_request(self, data: Any, template: dict) -> Any:
        return data  # no templating here, just pass through

    def parse_response(self, raw_response: RawResponse) -> Any:
        try:
            return self.parse_fn(raw_response.data)
        except Exception as e:
            raise ParserError(f"Custom parser failed: {e}") from e

    def parse_stream_chunk(self, raw_chunk: RawResponse) -> Optional[Any]:
        try:
            return self.parse_fn(raw_chunk.data)
        except Exception:
            return None

    def get_content_type(self, raw_response: RawResponse) -> str:
        return raw_response.headers.get("content-type", "unknown")


# ============================================================================
# Simple Template Engine
# ============================================================================


class SimpleTemplateEngine(BaseTemplateEngine):
    """
    Minimal template engine.
    Replaces {{var}} placeholders in strings, recursively handles dicts/lists.
    """

    _pattern = re.compile(r"{{\s*(\w+)\s*}}")

    def __init__(self, strict: bool = True):
        """
        Args:
            strict: if True, missing keys raise ParserError.
                    if False, placeholders remain untouched.
        """
        self.strict = strict

    def render_template(self, template: Any, variables: Dict[str, Any]) -> Any:
        if isinstance(template, str):
            return self._render_string(template, variables)
        elif isinstance(template, dict):
            return {k: self.render_template(v, variables) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.render_template(v, variables) for v in template]
        else:
            return template

    def _render_string(self, template: str, variables: Dict[str, Any]) -> str:
        def replacer(match):
            key = match.group(1)
            if key in variables:
                return str(variables[key])
            elif self.strict:
                raise TemplateError(f"Missing key '{key}' in template variables")
            else:
                return match.group(0)  # leave as is

        return self._pattern.sub(replacer, template)


# ============================================================================
# Simple Auth methods
# ============================================================================


class ApiKeyAuth:
    """Simple API key authentication"""
    def __init__(self, header: str, key: str, prefix: str = ""):
        self.header = header
        self.key = key
        self.prefix = prefix

    def apply(self, headers: dict) -> dict:
        headers[self.header] = f"{self.prefix}{self.key}"
        return headers


class BearerAuth(ApiKeyAuth):
    """Bearer token shortcut"""
    def __init__(self, token: str):
        super().__init__(header="Authorization", key=token, prefix="Bearer ")


# ============================================================================
# Built-in Registrations
# ============================================================================


AuthRegistry = Registry()


# Register built-ins
TransportRegistry.register('http', HTTPTransport)
TransportRegistry.register('websocket', WebSocketTransport)
ParserRegistry.register('json', JSONResponseParser)
ParserRegistry.register('text', PlainTextResponseParser)
ParserRegistry.register('binary', BinaryResponseParser)
ParserRegistry.register('custom', CustomResponseParser)
TemplateRegistry.register("simple", SimpleTemplateEngine)
AuthRegistry.register("api_key", ApiKeyAuth)
AuthRegistry.register("bearer", BearerAuth)


# ============================================================================
# PlusRouter (Battieries Included)
# ============================================================================


class PlusRouter(BaseRouter):
    """Router with batteries-included transports, parsers, templating, and optional auth.
    
    Error handling:
    - Does not catch errors raised by transports, parsers, or templates.
    - These may raise TransportError, ParserError, AuthError, or TemplateError.
    - All such errors inherit from AgnomuxError, so you can catch that for a single umbrella.
    """

    def __init__(self, template_engine: str = "simple", strict_templates: bool = True):
        super().__init__()
        self.template_engine = TemplateRegistry.get(template_engine)(strict=strict_templates)
        self.auth_registry = AuthRegistry

    def quick_endpoint(
        self,
        name: str,
        url: str,
        request_template: Any,
        response_extraction: Optional[Dict[str, Any]] = None,
        transport: str = "http",
        parser: str = "json",
        auth: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Quickly register a common HTTP+JSON endpoint."""
        self.add_endpoint(
            name,
            {
                "transport": transport,
                "parser": parser,
                "url": url,
                "request_template": request_template,
                "response_extraction": response_extraction,
                "auth": auth,
            },
        )

    def _get_config(self, endpoint: str, **data) -> Dict[str, Any]:
        """Extend core config resolution with templating and optional auth."""
        config = self.endpoints[endpoint].copy()
        
        # Inject default template engine if not set
        if "request_template" in config and "template_engine" not in config:
            config["template_engine"] = "simple"

        # Apply auth if defined
        if "auth" in config:
            auth_cfg = config["auth"]
            if isinstance(auth_cfg, dict):
                auth_type = auth_cfg.pop("type")
                auth_class = self.auth_registry.get(auth_type)
                auth = auth_class(**auth_cfg)

                # Apply to headers (create if missing)
                headers = config.get("headers", {})
                config["headers"] = auth.apply(headers)

        return config


# Export the enhanced router
Router = PlusRouter

# ============================================================================
# Public API
# ============================================================================

__all__ = ['Router', 'TransportRegistry', 'ParserRegistry', 'AgnomuxError',
           'BaseParser', 'JSONResponseParser', 'PlainTextResponseParser',
           'BinaryResponseParser', 'CustomResponseParser', 'TransportError',
           'ParserError', 'AuthError', 'TemplateError']


# ============================================================================
# Minimal CLI for testing
# ============================================================================

if __name__ == "__main__":
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Agnomux2 Plus CLI")
    parser.add_argument("url", help="Endpoint URL to send request to")
    parser.add_argument("data", help="Request data (JSON string)")
    parser.add_argument("--endpoint", default="test", help="Endpoint name (default: test)")
    parser.add_argument("--method", default="POST", help="HTTP method (default: POST)")
    parser.add_argument("--stream", action="store_true", help="Enable streaming mode")
    parser.add_argument("--asyncio", action="store_true", help="Use async send")

    args = parser.parse_args()

    router = PlusRouter()

    # Quick endpoint setup
    router.quick_endpoint(
        name=args.endpoint,
        url=args.url,
        request_template={},  # no templating in CLI example
        transport="http",
        parser="json",
    )

    # Parse data
    import json
    try:
        request_data = json.loads(args.data)
    except Exception:
        request_data = {"data": args.data}

    if args.stream:
        if args.asyncio:
            async def run():
                async for chunk in router.aroute_stream(args.endpoint, **request_data):
                    print("STREAM:", chunk)
            asyncio.run(run())
        else:
            for chunk in router.route_stream(args.endpoint, **request_data):
                print("STREAM:", chunk)
    else:
        if args.asyncio:
            async def run():
                resp = await router.aroute(args.endpoint, **request_data)
                print("RESPONSE:", resp)
            asyncio.run(run())
        else:
            resp = router.route(args.endpoint, **request_data)
            print("RESPONSE:", resp)