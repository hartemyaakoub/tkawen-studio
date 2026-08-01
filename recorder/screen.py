"""
TKAWEN Studio · Screen Recorder
Playwright captures vertical 1080x1920 video of platform flows.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Page


@dataclass
class ScreenStep:
    """One step in a recording flow."""
    url: Optional[str] = None         # navigate to this URL
    duration: float = 3.0             # seconds to record this step
    action: str = "wait"              # wait | scroll | click | hover | highlight | type
    selector: Optional[str] = None    # CSS selector for action target
    scroll_to: Optional[int] = None   # pixels (for scroll action)
    text: Optional[str] = None        # for type action
    smooth_scroll: bool = True


@dataclass
class RecordConfig:
    output_path: str = "output/screen.mp4"
    width: int = 1080
    height: int = 1920
    device_scale: float = 2.0
    headless: bool = True
    steps: list[ScreenStep] = field(default_factory=list)
    base_url: str = "https://mystoq.com"


# Smooth cursor injection script
CURSOR_JS = """
(() => {
  if (document.getElementById('tk-cursor')) return;
  const c = document.createElement('div');
  c.id = 'tk-cursor';
  c.style.cssText = `
    position: fixed; width: 32px; height: 32px;
    pointer-events: none; z-index: 999999;
    background: radial-gradient(circle, rgba(29,78,216,0.85) 0%, rgba(29,78,216,0) 70%);
    border-radius: 50%; transition: transform .35s cubic-bezier(.16,1,.3,1);
    transform: translate(-50%,-50%);
  `;
  document.body.appendChild(c);
  let x = window.innerWidth/2, y = window.innerHeight/2;
  c.style.left = x + 'px'; c.style.top = y + 'px';
  window.__tkMoveCursor = (nx, ny) => {
    c.style.left = nx + 'px'; c.style.top = ny + 'px';
  };
})();
"""

HIGHLIGHT_JS = """
(selector) => {
  const el = document.querySelector(selector);
  if (!el) return false;
  const r = el.getBoundingClientRect();
  const overlay = document.createElement('div');
  overlay.style.cssText = `
    position: fixed; pointer-events: none; z-index: 999998;
    left: ${r.left - 8}px; top: ${r.top - 8}px;
    width: ${r.width + 16}px; height: ${r.height + 16}px;
    border: 3px solid rgba(29,78,216,0.95);
    border-radius: 14px;
    box-shadow: 0 0 0 3px rgba(255,255,255,0.6), 0 12px 32px -6px rgba(29,78,216,0.45);
    animation: tk-pulse 1.4s ease-in-out infinite;
  `;
  document.body.appendChild(overlay);
  if (!document.getElementById('tk-anim')) {
    const s = document.createElement('style');
    s.id = 'tk-anim';
    s.textContent = '@keyframes tk-pulse { 50% { transform: scale(1.05); opacity: 0.7; } }';
    document.head.appendChild(s);
  }
  setTimeout(() => overlay.remove(), 4000);
  return true;
}
"""


async def execute_step(page: Page, step: ScreenStep, base_url: str) -> None:
    """Execute a single recording step."""
    if step.url:
        url = step.url if step.url.startswith("http") else f"{base_url}{step.url}"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.evaluate(CURSOR_JS)
        await asyncio.sleep(0.5)

    if step.action == "wait":
        await asyncio.sleep(step.duration)

    elif step.action == "scroll":
        if step.scroll_to is not None:
            if step.smooth_scroll:
                await page.evaluate(
                    f"window.scrollTo({{top: {step.scroll_to}, behavior: 'smooth'}})"
                )
            else:
                await page.evaluate(f"window.scrollTo(0, {step.scroll_to})")
        await asyncio.sleep(step.duration)

    elif step.action == "click":
        if step.selector:
            try:
                box = await page.locator(step.selector).first.bounding_box()
                if box:
                    cx = box["x"] + box["width"] / 2
                    cy = box["y"] + box["height"] / 2
                    await page.evaluate(f"window.__tkMoveCursor({cx}, {cy})")
                    await asyncio.sleep(0.6)
                await page.locator(step.selector).first.click(timeout=5000)
            except Exception as e:
                print(f"⚠️  click failed on {step.selector}: {e}")
        await asyncio.sleep(step.duration)

    elif step.action == "hover":
        if step.selector:
            try:
                await page.locator(step.selector).first.hover(timeout=5000)
            except Exception as e:
                print(f"⚠️  hover failed on {step.selector}: {e}")
        await asyncio.sleep(step.duration)

    elif step.action == "highlight":
        if step.selector:
            await page.evaluate(HIGHLIGHT_JS, step.selector)
        await asyncio.sleep(step.duration)

    elif step.action == "type":
        if step.selector and step.text:
            try:
                await page.locator(step.selector).first.click(timeout=5000)
                await page.keyboard.type(step.text, delay=80)
            except Exception as e:
                print(f"⚠️  type failed on {step.selector}: {e}")
        await asyncio.sleep(step.duration)


async def record(config: RecordConfig) -> dict:
    """Record screen video following the steps in config."""
    Path(config.output_path).parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.headless)
        context = await browser.new_context(
            viewport={"width": config.width // 2, "height": config.height // 2},
            device_scale_factor=config.device_scale,
            record_video_dir=str(Path(config.output_path).parent),
            record_video_size={"width": config.width, "height": config.height},
        )
        page = await context.new_page()

        try:
            for step in config.steps:
                await execute_step(page, step, config.base_url)

            video_path = await page.video.path() if page.video else None
        finally:
            await context.close()
            await browser.close()

        if video_path and video_path != config.output_path:
            Path(video_path).rename(config.output_path)

    return {
        "ok": Path(config.output_path).exists(),
        "path": config.output_path,
        "size_bytes": Path(config.output_path).stat().st_size if Path(config.output_path).exists() else 0,
    }


# ─── CLI ───
if __name__ == "__main__":
    import argparse
    import json
    import yaml

    parser = argparse.ArgumentParser(description="TKAWEN Studio · Screen Recorder")
    parser.add_argument("--flow", required=True, help="YAML flow file")
    parser.add_argument("--out", default="output/screen.mp4")
    parser.add_argument("--no-headless", action="store_true")
    args = parser.parse_args()

    with open(args.flow, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    config = RecordConfig(
        output_path=args.out,
        headless=not args.no_headless,
        base_url=data.get("base_url", "https://mystoq.com"),
        steps=[ScreenStep(**s) for s in data["steps"]],
    )

    result = asyncio.run(record(config))
    print(json.dumps(result, ensure_ascii=False, indent=2))
