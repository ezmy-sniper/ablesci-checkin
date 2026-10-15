"""科研通签到：python checkin.py login / run。"""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parent
ACTION = re.compile(r"^(?:今日打卡签到|每日签到|立即签到|点击签到|签到)(?:\s*[+＋]?\d+\s*积分)?$")
DONE = re.compile(r"^(?:今日已签到|今天已签到|已签到|签到成功)[！!。\s]*$")


def visible_matches(page, selector, pattern=None):
    items = page.locator(selector)
    result = []
    for i in range(items.count()):
        item = items.nth(i)
        if item.is_visible() and (pattern is None or pattern.fullmatch(item.inner_text().strip())):
            result.append(item)
    return result


def signed(page, cfg):
    # Only inspect controls or configured personal status, never the homepage activity feed.
    if cfg.get("signed_selector"):
        return bool(visible_matches(page, cfg["signed_selector"]))
    if cfg.get('button_selector') == '.fly-signin button.btn-sign':
        # Verified logged-in template: after signing, the server omits sign-no
        # while retaining the personal balance and consecutive-day counter.
        if (visible_matches(page, '.fly-signin #sign-count')
                and visible_matches(page, '.fly-signin #user-point-now')
                and page.locator('.fly-signin .sign-no').count() == 0):
            return True
    return bool(visible_matches(page, 'button, a, [role="button"], input[type="button"]', DONE))


def checkin(page, cfg):
    if signed(page, cfg):
        return "今日已签到"
    if '/site/login' in page.url:
        raise RuntimeError("登录已失效，请重新运行 login")
    selector = cfg.get("button_selector")
    matches = visible_matches(page, selector) if selector else visible_matches(
        page, 'button, a, [role="button"]', ACTION)
    if len(matches) != 1:
        raise RuntimeError(f"发现 {len(matches)} 个签到按钮；请检查登录状态或在 config.json 配置唯一的 button_selector")
    if selector == '.fly-signin button.btn-sign':
        # Observe the request made by the site's button, including its CSRF handling.
        with page.expect_response(lambda r: r.url.split('?')[0] == 'https://www.ablesci.com/user/sign', timeout=30000) as response_info:
            matches[0].click(timeout=15000)
        response = response_info.value
        if not response.ok:
            raise RuntimeError(f'签到请求失败：HTTP {response.status}')
        result = response.json()
        if result.get('code') == 0:
            return '签到已确认（网站返回成功）'
        raise RuntimeError('网站未确认签到成功，请使用 --headed 查看页面提示')
    matches[0].click(timeout=15000)
    deadline = time.monotonic() + 25
    while time.monotonic() < deadline:
        if signed(page, cfg):
            return "签到已确认"
        # Website's own transient messages, not other users' sign-in records.
        messages = visible_matches(page, '.layui-layer-content, [role="alert"]')
        if any(re.search(r"签到成功|(?:今日|今天).*已签到", m.inner_text()) for m in messages):
            return "签到已确认"
        page.wait_for_timeout(250)
    raise RuntimeError("点击后未获得明确成功提示；请人工查看，程序不会将点击本身当作成功")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['login', 'run'])
    parser.add_argument('--headed', action='store_true', help='显示浏览器以便排查')
    args = parser.parse_args()
    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[
        logging.StreamHandler(), RotatingFileHandler(logs / 'checkin.log', maxBytes=1000000, backupCount=3, encoding='utf-8')])
    try:
        from playwright.sync_api import sync_playwright
        cfg = json.loads((ROOT / 'config.json').read_text(encoding='utf-8-sig'))
        from urllib.parse import urlparse
        url = cfg['url']
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname != 'www.ablesci.com':
            raise ValueError('url 必须是 https://www.ablesci.com 下的页面')
        state = ROOT / 'session.json'
        if args.command == 'run' and not state.exists():
            raise RuntimeError('尚未保存登录状态，请先运行 login')
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=args.command != 'login' and not args.headed)
            context = browser.new_context(storage_state=str(state) if state.exists() else None,
                                          locale='zh-CN', timezone_id='Asia/Shanghai')
            page = context.new_page()
            try:
                page.goto('https://www.ablesci.com/site/login' if args.command == 'login' else url,
                          wait_until='domcontentloaded', timeout=60000)
                if args.command == 'login':
                    input('请在浏览器中完成登录（含验证码），然后回到这里按回车保存：')
                    page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    if '/site/login' in page.url or page.locator('a[href="https://www.ablesci.com/site/login"]').filter(has_text='登录').count():
                        raise RuntimeError('仍检测到登录入口，未保存，请确认已登录')
                    context.storage_state(path=str(state))
                    logging.info('登录状态已保存；可运行 run --headed 验证签到')
                else:
                    page.wait_for_timeout(1500)
                    logging.info(checkin(page, cfg))
                    context.storage_state(path=str(state))
            finally:
                context.close()
                browser.close()
        return 0
    except Exception as exc:
        logging.error('%s', exc)
        return 1


if __name__ == '__main__':
    sys.exit(main())
