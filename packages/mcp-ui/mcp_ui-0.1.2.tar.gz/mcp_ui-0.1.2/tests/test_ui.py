
import pytest

from mcp_ui import (
    create_ui_resource,
    RawHtmlContent,
    ExternalUrlContent,
    RemoteDomContent,
    ui_action_result_tool_call,
    ui_action_result_prompt,
    ui_action_result_link,
    ui_action_result_intent,
    ui_action_result_notification,
    CreateUIResourceOptions,
)


def test_create_ui_resource_with_html():
    options = CreateUIResourceOptions(
        uri="ui://test-html",
        content=RawHtmlContent(type="rawHtml", htmlString="<h1>Hello</h1>"),
        encoding="text",
    )
    resource = create_ui_resource(options)

    assert resource["type"] == "resource"
    assert resource["resource"]["mimeType"] == "text/html"
    assert resource["resource"]["text"] == "<h1>Hello</h1>"


def test_create_ui_resource_with_external_url():
    options = CreateUIResourceOptions(
        uri="ui://test-url",
        content=ExternalUrlContent(type="externalUrl", iframeUrl="https://example.com"),
        encoding="text",
    )
    resource = create_ui_resource(options)

    assert resource["resource"]["mimeType"] == "text/uri-list"
    assert resource["resource"]["text"] == "https://example.com"


def test_create_ui_resource_with_remote_dom_blob():
    options = CreateUIResourceOptions(
        uri="ui://test-remote",
        content=RemoteDomContent(type="remoteDom", script="console.log('hi')", framework="react"),
        encoding="blob",
    )
    resource = create_ui_resource(options)

    assert resource["resource"]["mimeType"].startswith(
        "application/vnd.mcp-ui.remote-dom+javascript; framework=react"
    )
    assert "blob" in resource["resource"]


def test_ui_action_results():
    tool_call = ui_action_result_tool_call("myTool", {"param": 1})
    assert tool_call.payload["toolName"] == "myTool"

    prompt = ui_action_result_prompt("Enter value")
    assert prompt.payload["prompt"] == "Enter value"

    link = ui_action_result_link("https://example.com")
    assert link.payload["url"] == "https://example.com"

    intent = ui_action_result_intent("open", {"id": 123})
    assert intent.payload["intent"] == "open"
    assert intent.payload["params"]["id"] == 123

    notification = ui_action_result_notification("Done!")
    assert notification.payload["message"] == "Done!"
