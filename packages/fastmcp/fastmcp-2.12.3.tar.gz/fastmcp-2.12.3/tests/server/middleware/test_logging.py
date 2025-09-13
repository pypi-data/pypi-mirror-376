"""Tests for logging middleware."""

import datetime
import json
import logging
from typing import Any, Literal, TypeVar
from unittest.mock import AsyncMock, MagicMock

import mcp
import mcp.types
import pytest
from inline_snapshot import snapshot
from pydantic import AnyUrl

from fastmcp.resources.template import ResourceTemplate
from fastmcp.server.middleware.logging import (
    LoggingMiddleware,
    StructuredLoggingMiddleware,
)
from fastmcp.server.middleware.middleware import CallNext, MiddlewareContext
from fastmcp.server.server import FastMCP

FIXED_DATE = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)

T = TypeVar("T")


def new_mock_context(
    message: T,
    method: str | None = None,
    source: Literal["server", "client"] | None = None,
    type: Literal["request", "notification"] | None = None,
) -> MiddlewareContext[T]:
    """Create a new mock middleware context."""
    context = MagicMock(spec=MiddlewareContext[T])
    context.method = method or "test_method"
    context.source = source or "client"
    context.type = type or "request"
    context.message = message
    context.timestamp = FIXED_DATE
    return context


@pytest.fixture
def mock_context():
    """Create a mock middleware context."""

    return new_mock_context(
        message=mcp.types.CallToolRequest(
            method="tools/call",
            params=mcp.types.CallToolRequestParams(
                name="test_method",
                arguments={"param": "value"},
            ),
        )
    )


@pytest.fixture
def mock_call_next() -> AsyncMock:
    """Create a mock call_next function."""
    return AsyncMock(return_value="test_result")


class TestLoggingMiddleware:
    """Test logging middleware functionality."""

    def test_init_default(self):
        """Test default initialization."""
        middleware = LoggingMiddleware()
        assert middleware.logger.name == "fastmcp.requests"
        assert middleware.log_level == logging.INFO
        assert middleware.include_payloads is False
        assert middleware.max_payload_length == 1000

    def test_init_custom(self):
        """Test custom initialization."""
        logger = logging.getLogger("custom")
        middleware = LoggingMiddleware(
            logger=logger,
            log_level=logging.DEBUG,
            include_payloads=True,
            max_payload_length=500,
        )
        assert middleware.logger is logger
        assert middleware.log_level == logging.DEBUG
        assert middleware.include_payloads is True
        assert middleware.max_payload_length == 500

    def test_format_message_without_payloads(
        self, mock_context: MiddlewareContext[Any]
    ):
        """Test message formatting without payloads."""
        middleware = LoggingMiddleware()
        formatted = middleware._format_message(mock_context)

        assert "source=client" in formatted
        assert "type=request" in formatted
        assert "method=test_method" in formatted
        assert "payload=" not in formatted

    def test_format_message_with_payloads(self, mock_context: MiddlewareContext[Any]):
        """Test message formatting with payloads."""
        middleware = LoggingMiddleware(include_payloads=True)
        formatted = middleware._format_message(mock_context)

        assert formatted == snapshot(
            'source=client type=request method=test_method payload={"method":"tools/call","params":{"_meta":null,"name":"test_method","arguments":{"param":"value"}}}'
        )

    def test_format_message_long_payload(self, mock_context: MiddlewareContext[Any]):
        """Test message formatting with long payload truncation."""
        middleware = LoggingMiddleware(include_payloads=True, max_payload_length=10)
        formatted = middleware._format_message(mock_context)

        assert "payload=" in formatted
        assert "..." in formatted

    async def test_on_message_success(
        self,
        mock_context: MiddlewareContext[Any],
        caplog: pytest.LogCaptureFixture,
    ):
        """Test logging successful messages."""
        middleware = LoggingMiddleware()
        mock_call_next = AsyncMock(return_value="test_result")

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"
        assert mock_call_next.called
        assert "Processing message:" in caplog.text
        assert "Completed message: test_method" in caplog.text

    async def test_on_message_failure(
        self, mock_context: MiddlewareContext[Any], caplog: pytest.LogCaptureFixture
    ):
        """Test logging failed messages."""
        middleware = LoggingMiddleware()
        mock_call_next = AsyncMock(side_effect=ValueError("test error"))

        with caplog.at_level(logging.INFO):
            with pytest.raises(ValueError):
                await middleware.on_message(mock_context, mock_call_next)

        assert "Processing message:" in caplog.text
        assert "Failed message: test_method - test error" in caplog.text


class TestStructuredLoggingMiddleware:
    """Test structured logging middleware functionality."""

    def test_init_default(self):
        """Test default initialization."""
        middleware = StructuredLoggingMiddleware()
        assert middleware.logger.name == "fastmcp.structured"
        assert middleware.log_level == logging.INFO
        assert middleware.include_payloads is False

    def test_create_log_entry_basic(self, mock_context: MiddlewareContext[Any]):
        """Test creating basic log entry."""
        middleware = StructuredLoggingMiddleware()
        entry = middleware._create_log_entry(mock_context, "test_event")

        assert entry == snapshot(
            {
                "event": "test_event",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
            }
        )

    def test_create_log_entry_with_payload(self, mock_context: MiddlewareContext[Any]):
        """Test creating log entry with payload."""
        middleware = StructuredLoggingMiddleware(include_payloads=True)
        entry = middleware._create_log_entry(mock_context, "test_event")

        assert entry == snapshot(
            {
                "event": "test_event",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "payload": '{"method":"tools/call","params":{"_meta":null,"name":"test_method","arguments":{"param":"value"}}}',
            }
        )

    def test_create_log_entry_with_extra_fields(
        self, mock_context: MiddlewareContext[Any]
    ):
        """Test creating log entry with extra fields."""
        middleware = StructuredLoggingMiddleware()
        entry = middleware._create_log_entry(
            mock_context, "test_event", extra_field="extra_value"
        )

        assert entry["extra_field"] == "extra_value"

    async def test_on_message_success(
        self,
        mock_context: MiddlewareContext[Any],
        mock_call_next: CallNext[Any, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        """Test structured logging of successful messages."""
        middleware = StructuredLoggingMiddleware()

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"

        # Check that we have structured JSON logs
        log_lines = [record.message for record in caplog.records]

        assert len(log_lines) == 2  # start and success entries

        assert json.loads(log_lines[0]) == snapshot(
            {
                "event": "request_start",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
            }
        )

        assert json.loads(log_lines[1]) == snapshot(
            {
                "event": "request_success",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "result_type": "str",
            }
        )

    async def test_on_message_failure(
        self, mock_context: MiddlewareContext[Any], caplog: pytest.LogCaptureFixture
    ):
        """Test structured logging of failed messages."""
        middleware = StructuredLoggingMiddleware()
        mock_call_next = AsyncMock(side_effect=ValueError("test error"))

        with caplog.at_level(logging.INFO):
            with pytest.raises(ValueError):
                await middleware.on_message(mock_context, mock_call_next)

        # Check that we have structured JSON logs
        log_lines = [record.message for record in caplog.records]
        assert len(log_lines) == 2  # start and error entries

        start_entry = json.loads(log_lines[0])
        assert start_entry["event"] == "request_start"

        assert json.loads(log_lines[1]) == snapshot(
            {
                "event": "request_error",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "error_type": "ValueError",
                "error_message": "test error",
            }
        )

    async def test_on_message_with_pydantic_types_in_payload(
        self,
        mock_call_next: CallNext[Any, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        """Ensure Pydantic AnyUrl in payload serializes correctly when include_payloads=True."""

        mock_context = new_mock_context(
            message=mcp.types.ReadResourceRequest(
                method="resources/read",
                params=mcp.types.ReadResourceRequestParams(
                    uri=AnyUrl("test://example/1"),
                ),
            )
        )

        middleware = StructuredLoggingMiddleware(include_payloads=True)

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"

        log_lines = [record.message for record in caplog.records]

        assert len(log_lines) == 2
        assert json.loads(log_lines[0]) == snapshot(
            {
                "event": "request_start",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "payload": '{"method":"resources/read","params":{"_meta":null,"uri":"test://example/1"}}',
            }
        )
        assert json.loads(log_lines[1]) == snapshot(
            {
                "event": "request_success",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "result_type": "str",
                "payload": '{"method":"resources/read","params":{"_meta":null,"uri":"test://example/1"}}',
            }
        )

    async def test_on_message_with_resource_template_in_payload(
        self,
        mock_call_next: CallNext[Any, Any],
        caplog: pytest.LogCaptureFixture,
    ):
        """Ensure ResourceTemplate in payload serializes via pydantic conversion without errors."""

        mock_context = new_mock_context(
            message=ResourceTemplate(
                name="tmpl",
                uri_template="tmpl://{id}",
                parameters={"id": {"type": "string"}},
            )
        )

        middleware = StructuredLoggingMiddleware(include_payloads=True)

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"

        log_lines = [record.message for record in caplog.records]
        assert len(log_lines) == 2
        assert json.loads(log_lines[0]) == snapshot(
            {
                "event": "request_start",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "payload": '{"name":"tmpl","title":null,"description":null,"tags":[],"meta":null,"enabled":true,"uri_template":"tmpl://{id}","mime_type":"text/plain","parameters":{"id":{"type":"string"}},"annotations":null}',
            }
        )

    async def test_on_message_with_nonserializable_payload_falls_back_to_str(
        self, mock_call_next: CallNext[Any, Any], caplog: pytest.LogCaptureFixture
    ):
        """Ensure non-JSONable objects fall back to string serialization in payload."""

        class NonSerializable:
            def __str__(self) -> str:
                return "NON_SERIALIZABLE"

        mock_context = new_mock_context(
            message=mcp.types.CallToolRequest(
                method="tools/call",
                params=mcp.types.CallToolRequestParams(
                    name="test_method",
                    arguments={"obj": NonSerializable()},
                ),
            )
        )

        middleware = StructuredLoggingMiddleware(include_payloads=True)

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"

        log_lines = [record.message for record in caplog.records]
        assert len(log_lines) >= 2
        assert json.loads(log_lines[0]) == snapshot(
            {
                "event": "request_start",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "payload": '{"method":"tools/call","params":{"_meta":null,"name":"test_method","arguments":{"obj":"NON_SERIALIZABLE"}}}',
            }
        )

    async def test_on_message_with_custom_serializer_applied(
        self, mock_call_next: CallNext[Any, Any], caplog: pytest.LogCaptureFixture
    ):
        """Ensure a custom serializer is used for non-JSONable payloads."""

        # Provide a serializer that replaces entire payload with a fixed string
        def custom_serializer(_: Any) -> str:
            return "CUSTOM_PAYLOAD"

        mock_context = new_mock_context(
            message=mcp.types.CallToolRequest(
                method="tools/call",
                params=mcp.types.CallToolRequestParams(
                    name="test_method",
                    arguments={"obj": "OBJECT"},
                ),
            )
        )

        middleware = StructuredLoggingMiddleware(
            include_payloads=True, payload_serializer=custom_serializer
        )

        with caplog.at_level(logging.INFO):
            result = await middleware.on_message(mock_context, mock_call_next)

        assert result == "test_result"

        log_lines = [record.message for record in caplog.records]
        assert len(log_lines) >= 2
        assert json.loads(log_lines[0]) == snapshot(
            {
                "event": "request_start",
                "timestamp": "2023-01-01T00:00:00+00:00",
                "source": "client",
                "type": "request",
                "method": "test_method",
                "payload": "CUSTOM_PAYLOAD",
            }
        )


@pytest.fixture
def logging_server():
    """Create a FastMCP server specifically for logging middleware tests."""
    from fastmcp import FastMCP

    mcp = FastMCP("LoggingTestServer")

    @mcp.tool
    def simple_operation(data: str) -> str:
        """A simple operation for testing logging."""
        return f"Processed: {data}"

    @mcp.tool
    def complex_operation(items: list[str], mode: str = "default") -> dict:
        """A complex operation with structured data."""
        return {"processed_items": len(items), "mode": mode, "result": "success"}

    @mcp.tool
    def operation_with_error(should_fail: bool = False) -> str:
        """An operation that can be made to fail."""
        if should_fail:
            raise ValueError("Operation failed intentionally")
        return "Operation completed successfully"

    @mcp.resource("log://test")
    def test_resource() -> str:
        """A test resource for logging."""
        return "Test resource content"

    @mcp.prompt
    def test_prompt() -> str:
        """A test prompt for logging."""
        return "Test prompt content"

    return mcp


class TestLoggingMiddlewareIntegration:
    """Integration tests for logging middleware with real FastMCP server."""

    async def test_logging_middleware_logs_successful_operations(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test that logging middleware captures successful operations."""
        from fastmcp.client import Client

        logging_server.add_middleware(LoggingMiddleware(methods=["tools/call"]))

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                await client.call_tool("simple_operation", {"data": "test_data"})
                await client.call_tool(
                    "complex_operation", {"items": ["a", "b", "c"], "mode": "batch"}
                )

        log_text = caplog.text

        # Should have processing and completion logs for both operations
        assert "Processing message:" in log_text
        assert "Completed message: tools/call" in log_text

        # Should have captured both tool calls
        processing_count = log_text.count("Processing message:")
        completion_count = log_text.count("Completed message:")
        assert processing_count == 2
        assert completion_count == 2

    async def test_logging_middleware_logs_failures(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test that logging middleware captures failed operations."""
        from fastmcp.client import Client

        logging_server.add_middleware(LoggingMiddleware(methods=["tools/call"]))

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                # This should fail and be logged
                with pytest.raises(Exception):
                    await client.call_tool(
                        "operation_with_error", {"should_fail": True}
                    )

        log_text = caplog.text

        # Should have processing and failure logs
        assert "Processing message:" in log_text
        assert "Failed message: tools/call" in log_text

    async def test_logging_middleware_with_payloads(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test logging middleware when configured to include payloads."""
        from fastmcp.client import Client

        logging_server.add_middleware(
            LoggingMiddleware(
                include_payloads=True, max_payload_length=500, methods=["tools/call"]
            )
        )

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                await client.call_tool("simple_operation", {"data": "payload_test"})

        log_text = caplog.text

        # Should include payload information
        assert "Processing message:" in log_text
        assert "payload=" in log_text

    async def test_structured_logging_middleware_produces_json(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test that structured logging middleware produces parseable JSON logs."""
        import json

        from fastmcp.client import Client

        logging_server.add_middleware(
            StructuredLoggingMiddleware(include_payloads=True, methods=["tools/call"])
        )

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                await client.call_tool("simple_operation", {"data": "json_test"})

        # Extract JSON log entries
        log_lines = [
            record.message
            for record in caplog.records
            if record.name == "fastmcp.structured"
        ]

        assert len(log_lines) >= 2  # Should have start and success entries

        # Each log line should be valid JSON
        for line in log_lines:
            log_entry = json.loads(line)
            assert "event" in log_entry
            assert "timestamp" in log_entry
            assert "source" in log_entry
            assert "type" in log_entry
            assert "method" in log_entry

    async def test_structured_logging_middleware_handles_errors(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test structured logging of errors with JSON format."""
        import json

        from fastmcp.client import Client

        logging_server.add_middleware(
            StructuredLoggingMiddleware(methods=["tools/call"])
        )

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                with pytest.raises(Exception):
                    await client.call_tool(
                        "operation_with_error", {"should_fail": True}
                    )

        # Extract JSON log entries
        log_lines = [
            record.message
            for record in caplog.records
            if record.name == "fastmcp.structured"
        ]

        # Should have start and error entries
        assert len(log_lines) >= 2

        # Find the error entry
        error_entries = []
        for line in log_lines:
            log_entry = json.loads(line)
            if log_entry.get("event") == "request_error":
                error_entries.append(log_entry)

        assert len(error_entries) == 1
        error_entry = error_entries[0]
        assert "error_type" in error_entry
        assert "error_message" in error_entry

    async def test_logging_middleware_with_different_operations(
        self, logging_server: FastMCP, caplog: pytest.LogCaptureFixture
    ):
        """Test logging middleware with various MCP operations."""
        from fastmcp.client import Client

        logging_server.add_middleware(
            LoggingMiddleware(
                methods=[
                    "tools/call",
                    "resources/list",
                    "prompts/get",
                    "resources/read",
                ]
            )
        )

        with caplog.at_level(logging.INFO):
            async with Client(logging_server) as client:
                # Test different operation types
                await client.call_tool("simple_operation", {"data": "test"})
                await client.read_resource("log://test")
                await client.get_prompt("test_prompt")
                await client.list_resources()

        log_text = caplog.text

        # Should have logs for all different operation types
        # Note: Different operations may have different method names
        processing_count = log_text.count("Processing message:")
        completion_count = log_text.count("Completed message:")

        # Should have processed all 4 operations
        assert processing_count == 4
        assert completion_count == 4

    async def test_logging_middleware_custom_configuration(
        self, logging_server: FastMCP
    ):
        """Test logging middleware with custom logger configuration."""
        import io
        import logging

        from fastmcp.client import Client

        # Create custom logger
        log_buffer = io.StringIO()
        handler = logging.StreamHandler(log_buffer)
        custom_logger = logging.getLogger("custom_logging_test")
        custom_logger.addHandler(handler)
        custom_logger.setLevel(logging.DEBUG)

        logging_server.add_middleware(
            LoggingMiddleware(
                logger=custom_logger,
                log_level=logging.DEBUG,
                include_payloads=True,
                methods=["tools/call"],
            )
        )

        async with Client(logging_server) as client:
            await client.call_tool("simple_operation", {"data": "custom_test"})

        # Check that our custom logger captured the logs
        log_output = log_buffer.getvalue()
        assert "Processing message:" in log_output
        assert "payload=" in log_output
