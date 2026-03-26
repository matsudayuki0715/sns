"""DrissionPage でSNS各プラットフォームの公開メトリクスを取得する

ブラウザが自動で開き、各ページにアクセスして数値をスクレイピングします。
初回はブラウザのパスを聞かれる場合があります（Chromeを選択）。
"""

import json
import re
import sys
import time
import os
from pathlib import Path

# Windows cp932 対策
sys.stdout.reconfigure(encoding="utf-8")

from DrissionPage import Chromium

ACCOUNTS = {
    "tiktok": {
        "url": "https://www.tiktok.com/@kiq_robotics",
        "name": "TikTok",
    },
    "instagram": {
        "url": "https://www.instagram.com/kiq_robotics/",
        "name": "Instagram",
    },
    "facebook": {
        "url": "https://www.facebook.com/kiqrobotics/",
        "name": "Facebook",
    },
    "x": {
        "url": "https://x.com/KiQ_Robotics",
        "name": "X (Twitter)",
    },
}


def parse_count(text: str) -> int | str:
    """'1.2万' や '1,234' や '1.2K' などを数値に変換する"""
    if not text:
        return "取得失敗"
    text = text.strip().replace(",", "").replace(" ", "")

    # 日本語表記
    if "万" in text:
        num = float(text.replace("万", ""))
        return int(num * 10000)
    if "億" in text:
        num = float(text.replace("億", ""))
        return int(num * 100000000)

    # 英語表記
    if text.upper().endswith("K"):
        return int(float(text[:-1]) * 1000)
    if text.upper().endswith("M"):
        return int(float(text[:-1]) * 1000000)

    # 数値のみ
    try:
        return int(float(text))
    except ValueError:
        return text


def fetch_tiktok(tab) -> dict:
    """TikTokのプロフィール情報を取得"""
    tab.get("https://www.tiktok.com/@kiq_robotics")
    time.sleep(5)

    result = {"platform": "TikTok", "handle": "@kiq_robotics"}

    try:
        # フォロワー数
        follower_el = tab.ele("xpath://strong[@data-e2e='followers-count']", timeout=10)
        result["followers"] = parse_count(follower_el.text) if follower_el else "取得失敗"
    except Exception:
        result["followers"] = "取得失敗"

    try:
        # フォロー数
        following_el = tab.ele("xpath://strong[@data-e2e='following-count']", timeout=5)
        result["following"] = parse_count(following_el.text) if following_el else "取得失敗"
    except Exception:
        result["following"] = "取得失敗"

    try:
        # いいね数
        likes_el = tab.ele("xpath://strong[@data-e2e='likes-count']", timeout=5)
        result["total_likes"] = parse_count(likes_el.text) if likes_el else "取得失敗"
    except Exception:
        result["total_likes"] = "取得失敗"

    # 動画の再生数（見えている範囲）
    try:
        view_els = tab.eles("xpath://strong[@data-e2e='video-views']", timeout=5)
        if view_els:
            views = [parse_count(el.text) for el in view_els[:10]]
            numeric_views = [v for v in views if isinstance(v, int)]
            result["recent_video_views"] = views
            result["avg_recent_views"] = sum(numeric_views) // len(numeric_views) if numeric_views else "取得失敗"
    except Exception:
        pass

    return result


def fetch_instagram(tab) -> dict:
    """Instagramのプロフィール情報を取得"""
    tab.get("https://www.instagram.com/kiq_robotics/")
    time.sleep(5)

    result = {"platform": "Instagram", "handle": "@kiq_robotics"}

    try:
        # メタデータから取得（ページソースにJSON-LDやmetaタグがある）
        page_text = tab.html
        # "XX followers" パターン
        follower_match = re.search(r'"edge_followed_by":\s*\{"count":\s*(\d+)\}', page_text)
        if follower_match:
            result["followers"] = int(follower_match.group(1))
        else:
            # metaタグから
            meta_match = re.search(r'([\d,.]+[KMkm万億]?)\s*[Ff]ollowers', page_text)
            if meta_match:
                result["followers"] = parse_count(meta_match.group(1))
            else:
                # UIから直接取得を試みる
                header = tab.ele("tag:header", timeout=10)
                if header:
                    spans = header.eles("tag:span")
                    for span in spans:
                        text = span.text
                        if "follower" in text.lower() or "フォロワー" in text:
                            num = re.search(r'([\d,.]+[KMkm万億]?)', text)
                            if num:
                                result["followers"] = parse_count(num.group(1))
                                break
    except Exception:
        result["followers"] = "取得失敗"

    try:
        post_match = re.search(r'"edge_owner_to_timeline_media":\s*\{"count":\s*(\d+)', page_text)
        if post_match:
            result["posts"] = int(post_match.group(1))
        else:
            meta_match = re.search(r'([\d,.]+)\s*[Pp]osts', page_text)
            if meta_match:
                result["posts"] = parse_count(meta_match.group(1))
    except Exception:
        result["posts"] = "取得失敗"

    return result


def fetch_facebook(tab) -> dict:
    """Facebookページの情報を取得"""
    tab.get("https://www.facebook.com/kiqrobotics/")
    time.sleep(5)

    result = {"platform": "Facebook", "handle": "kiqrobotics"}

    try:
        page_text = tab.html
        # 「いいね」数
        like_match = re.search(r'([\d,.]+[KMkm万億]?)\s*(?:人が「いいね！」|likes?)', page_text, re.IGNORECASE)
        if like_match:
            result["page_likes"] = parse_count(like_match.group(1))

        # フォロワー数
        follower_match = re.search(r'([\d,.]+[KMkm万億]?)\s*(?:人がフォロー|followers?)', page_text, re.IGNORECASE)
        if follower_match:
            result["followers"] = parse_count(follower_match.group(1))
    except Exception:
        result["followers"] = "取得失敗"

    return result


def fetch_x(tab) -> dict:
    """X (Twitter) のプロフィール情報を取得"""
    tab.get("https://x.com/KiQ_Robotics")
    time.sleep(5)

    result = {"platform": "X (Twitter)", "handle": "@KiQ_Robotics"}

    try:
        page_text = tab.html

        # フォロワー数（aria-label から取得）
        follower_link = tab.ele("xpath://a[contains(@href, '/verified_followers') or contains(@href, '/followers')]", timeout=10)
        if follower_link:
            label = follower_link.attr("aria-label") or follower_link.text
            num = re.search(r'([\d,.]+[KMkm万億]?)', label)
            if num:
                result["followers"] = parse_count(num.group(1))

        # フォロー数
        following_link = tab.ele("xpath://a[contains(@href, '/following')]", timeout=5)
        if following_link:
            label = following_link.attr("aria-label") or following_link.text
            num = re.search(r'([\d,.]+[KMkm万億]?)', label)
            if num:
                result["following"] = parse_count(num.group(1))

    except Exception:
        result["followers"] = "取得失敗"

    return result


def main():
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    print("\nブラウザを起動してSNSメトリクスを取得します...")
    print("※ ログイン画面が出た場合はスキップ/閉じてください\n")

    browser = Chromium()
    tab = browser.latest_tab

    all_results = {}
    fetchers = {
        "tiktok": fetch_tiktok,
        "instagram": fetch_instagram,
        "facebook": fetch_facebook,
        "x": fetch_x,
    }

    for key, fetcher in fetchers.items():
        name = ACCOUNTS[key]["name"]
        print(f"  {name} を取得中...")
        try:
            result = fetcher(tab)
            all_results[key] = result
            print(f"  ✓ {name}: {json.dumps(result, ensure_ascii=False, default=str)}")
        except Exception as e:
            print(f"  ✗ {name}: エラー - {e}")
            all_results[key] = {"platform": name, "error": str(e)}

        # レート制限回避のため少し待つ
        time.sleep(2)

    # 結果を保存
    with open(results_dir / "sns_metrics.json", "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)

    # 見やすいサマリーを表示
    print(f"\n{'='*60}")
    print("  SNSメトリクス サマリー")
    print(f"{'='*60}")
    for key, data in all_results.items():
        name = data.get("platform", key)
        followers = data.get("followers", "不明")
        extra = ""
        if "total_likes" in data:
            extra += f" / いいね合計: {data['total_likes']}"
        if "posts" in data:
            extra += f" / 投稿数: {data['posts']}"
        if "avg_recent_views" in data:
            extra += f" / 直近平均再生: {data['avg_recent_views']}"
        print(f"  {name:15s}: フォロワー {followers}{extra}")
    print(f"{'='*60}\n")
    print(f"  → results/sns_metrics.json に保存しました")

    browser.quit()


if __name__ == "__main__":
    main()
