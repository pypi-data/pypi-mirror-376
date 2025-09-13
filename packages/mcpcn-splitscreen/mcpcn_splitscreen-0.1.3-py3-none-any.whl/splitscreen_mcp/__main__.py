from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from .window_actions import (
    left_half_window, right_half_window,
    top_half_window, bottom_half_window,
    top_left_quadrant_window, top_right_quadrant_window,
    bottom_left_quadrant_window, bottom_right_quadrant_window,
    left_third_window, middle_third_window, right_third_window,
    left_two_thirds_window, right_two_thirds_window,
    maximise_window, minimise_window, fullscreen_window,
)

mcp = FastMCP("computer-split-screen")

def ok(msg: str) -> TextContent:
    return TextContent(type="text", text=msg)

@mcp.tool("left-half-screen", description="将当前聚焦的窗口移动到屏幕左半部分")
def left_half() -> TextContent:
    left_half_window()
    return ok("left-half: done")

@mcp.tool("right-half-screen", description="将当前聚焦的窗口移动到屏幕右半部分")
def right_half() -> TextContent:
    right_half_window()
    return ok("right-half: done")

@mcp.tool("top-half-screen", description="将当前聚焦的窗口移动到屏幕上半部分")
def top_half() -> TextContent:
    top_half_window()
    return ok("top-half: done")

@mcp.tool("bottom-half-screen", description="将当前聚焦的窗口移动到屏幕下半部分")
def bottom_half() -> TextContent:
    bottom_half_window()
    return ok("bottom-half: done")

@mcp.tool("top-left-screen", description="将当前聚焦的窗口移动到屏幕左上角四分之一区域")
def top_left() -> TextContent:
    top_left_quadrant_window()
    return ok("top-left: done")

@mcp.tool("top-right-screen", description="将当前聚焦的窗口移动到屏幕右上角四分之一区域")
def top_right() -> TextContent:
    top_right_quadrant_window()
    return ok("top-right: done")

@mcp.tool("bottom-left-screen", description="将当前聚焦的窗口移动到屏幕左下角四分之一区域")
def bottom_left() -> TextContent:
    bottom_left_quadrant_window()
    return ok("bottom-left: done")

@mcp.tool("bottom-right-screen", description="将当前聚焦的窗口移动到屏幕右下角四分之一区域")
def bottom_right() -> TextContent:
    bottom_right_quadrant_window()
    return ok("bottom-right: done")

# ===== 1/3和2/3分屏工具 =====
@mcp.tool("left-one-third-screen", description="将当前聚焦的窗口移动到屏幕左侧三分之一区域")
def left_third() -> TextContent:
    left_third_window()
    return ok("left-third: done")

@mcp.tool("middle-one-third-screen", description="将当前聚焦的窗口移动到屏幕中间三分之一区域")
def middle_third() -> TextContent:
    middle_third_window()
    return ok("middle-third: done")

@mcp.tool("right-one-third-screen", description="将当前聚焦的窗口移动到屏幕右侧三分之一区域")
def right_third() -> TextContent:
    right_third_window()
    return ok("right-third: done")

@mcp.tool("left-two-thirds-screen", description="将当前聚焦的窗口移动到屏幕左侧三分之二区域")
def left_two_thirds() -> TextContent:
    left_two_thirds_window()
    return ok("left-two-thirds: done")

@mcp.tool("right-two-thirds-screen", description="将当前聚焦的窗口移动到屏幕右侧三分之二区域")
def right_two_thirds() -> TextContent:
    right_two_thirds_window()
    return ok("right-two-thirds: done")

@mcp.tool("maximize-screen", description="最大化当前聚焦的窗口，保持边框和标题栏可见")
def maximize() -> TextContent:
    maximise_window()
    return ok("maximize: done")

@mcp.tool("fullscreen-screen", description="将当前聚焦的窗口设置为全屏模式。在macOS上使用无边框全屏，在Windows上使用标准最大化模式")
def fullscreen() -> TextContent:
    fullscreen_window()
    return ok("fullscreen: done")

@mcp.tool("minimize-screen", description="最小化当前聚焦的窗口，在Windows上发送到任务栏，在macOS上发送到Dock")
def minimize() -> TextContent:
    success = minimise_window()
    return ok("minimize: done" if success else "minimize: failed")

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
