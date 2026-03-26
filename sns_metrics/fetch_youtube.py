"""YouTube Data API v3 でチャンネル統計を取得する"""

import json
import os
import sys
from googleapiclient.discovery import build

# === 設定 ===
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")  # 環境変数 or .env から取得
CHANNEL_HANDLE = "@KiQ_Robotics_Corp."
# =============

def main():
    api_key = API_KEY
    # .env ファイルから読み込み（python-dotenv不要の簡易実装）
    if not api_key:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.startswith("YOUTUBE_API_KEY="):
                        api_key = line.strip().split("=", 1)[1]
    if not api_key:
        print("エラー: YOUTUBE_API_KEY を設定してください")
        print("sns_metrics/.env に YOUTUBE_API_KEY=xxxx を記載するか、環境変数を設定してください")
        sys.exit(1)

    youtube = build("youtube", "v3", developerKey=api_key)

    # ハンドルからチャンネルIDを取得
    search = youtube.search().list(
        part="snippet",
        q=CHANNEL_HANDLE,
        type="channel",
        maxResults=1,
    ).execute()

    if not search["items"]:
        print(f"チャンネルが見つかりません: {CHANNEL_HANDLE}")
        sys.exit(1)

    channel_id = search["items"][0]["snippet"]["channelId"]
    channel_title = search["items"][0]["snippet"]["title"]

    # チャンネル統計を取得
    channel = youtube.channels().list(
        part="statistics,snippet,contentDetails",
        id=channel_id,
    ).execute()

    stats = channel["items"][0]["statistics"]

    print(f"\n{'='*50}")
    print(f"  YouTube: {channel_title}")
    print(f"{'='*50}")
    print(f"  チャンネルID  : {channel_id}")
    print(f"  登録者数      : {int(stats.get('subscriberCount', 0)):,}")
    print(f"  総再生回数    : {int(stats.get('viewCount', 0)):,}")
    print(f"  動画数        : {int(stats.get('videoCount', 0)):,}")
    print(f"{'='*50}\n")

    # 最新動画の再生数も取得
    playlist_id = channel["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = youtube.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=10,
    ).execute()

    video_ids = [v["contentDetails"]["videoId"] for v in videos["items"]]
    video_details = youtube.videos().list(
        part="statistics,snippet",
        id=",".join(video_ids),
    ).execute()

    print("  最新10本の再生数:")
    print(f"  {'─'*46}")
    total_views = 0
    for v in video_details["items"]:
        title = v["snippet"]["title"][:30]
        views = int(v["statistics"].get("viewCount", 0))
        likes = int(v["statistics"].get("likeCount", 0))
        total_views += views
        print(f"  {views:>8,}再生 / {likes:>4,}いいね | {title}")

    avg_views = total_views // len(video_details["items"]) if video_details["items"] else 0
    print(f"  {'─'*46}")
    print(f"  平均再生数: {avg_views:,}\n")

    # 結果をJSONで保存
    result = {
        "platform": "YouTube",
        "channel_title": channel_title,
        "channel_id": channel_id,
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "recent_avg_views": avg_views,
    }
    with open("results/youtube.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("  → results/youtube.json に保存しました")


if __name__ == "__main__":
    main()
