import tweepy
import json
import time
import os
import random
import requests

# Twitter API v2 の認証情報
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANFvzwEAAAAAyd2XUJeqPRFPtgbNg%2FXcLfjcPr8%3DRrhDRkxP7LC9U03CtxLn1oOW5L7VPBv314c6Pv4UPQKw4C0REa"
API_KEY = "k6obonIZ2i6Q4xGnFLai6xyW4"
API_SECRET = "Vx56Qpr1vOt4UxkXfDG3Uxe4Cn899XCi4DiDzjSLauc5piuXm7"
ACCESS_TOKEN = "1796169192535965696-ZDn5Jy5sXUjzDSu4bkRkkJVSDGTi8w"
ACCESS_SECRET = "likhAJXnpxkSkBX9FtxnxVRrkutEzK5k7r0DZfadq3Wyj"

# 認証処理
client = tweepy.Client(
    bearer_token=BEARER_TOKEN,
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_SECRET,
    wait_on_rate_limit=True
)

# 監視するターゲットのTwitterユーザーID(3つ)
TARGET_USER_IDS = ["user1", "user2", "user3"]  # 監視するアカウントのID
current_index = 0  # どのアカウントを監視するか管理

# 送信履歴を保存するファイル
HISTORY_FILE = "replied_users.json"

# 送信履歴をロード
def load_replied_users():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                print("⚠️ JSONファイルが壊れているので初期化")
                return set()
    return set()

# 送信履歴を保存
def save_replied_users(replied_users):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(replied_users), f)

# 送信履歴を読み込む
replied_users = load_replied_users()

# リプライ候補のリスト
REPLY_MESSAGES = [
    "初めまして志波と申します🙇🏻‍♂️\nツイート拝見させていただきました🤲🏻\nぜひ良ければご相談乗らせてください🙌🏻",
    "初めまして志波と申します🙇🏻‍♂️\nツイート拝見させていただきました🤲🏻\n相談だけでも良いのでぜひお返事ください🙂‍↕️",
    "初めまして志波と申します🙇🏻‍♂️\n相談だけでもOKなのでぜひお返事ください🙌🏻"
]

# 取得する最新ツイートのID(アカウントごとに管理)
since_ids = {user_id: None for user_id in TARGET_USER_IDS}

# 無限ループで監視
while True:
    try:
        target_user = TARGET_USER_IDS[current_index]  # 現在の監視対象

        # 監視対象ユーザーのリプライツイートを取得
        query = f"from:{target_user}"
        tweets = client.search_recent_tweets(query=query, since_id=since_ids[target_user], tweet_fields=["conversation_id", "in_reply_to_user_id"], max_results=10)

        if tweets.data:
            for tweet in tweets.data:
                since_ids[target_user] = tweet.id  # 最新のツイートIDを保存

                # リプライであることを確認
                if tweet.in_reply_to_user_id:
                    original_tweet = client.get_tweet(tweet.conversation_id, tweet_fields=["author_id"])

                    # 監視対象が自分のリプライにリプライしている場合はスキップ
                    if original_tweet.data and original_tweet.data.author_id == target_user:
                        print(f"⚠️ {target_user} がツリー形式でリプライを続けているため無視")
                        continue  # スキップ

                    # すでにリプライを送った相手ならスキップ
                    if original_tweet.data and original_tweet.data.author_id in replied_users:
                        print("⚠️ すでにリプライ済みのツイートなのでスキップ")
                        continue

                    # ランダムでリプライを選択
                    reply_text = random.choice(REPLY_MESSAGES)

                    # リプライを送信
                    try:
                        client.create_tweet(
                            text=reply_text,
                            in_reply_to_tweet_id=original_tweet.data.id
                        )
                        print(f"💬 {original_tweet.data.author_id} へリプライ送信: {reply_text}")

                        # 送信履歴に追加
                        replied_users.add(original_tweet.data.author_id)
                        save_replied_users(replied_users)

                        # 1件リプライしたら1分待機
                        time.sleep(60)

                    except tweepy.TooManyRequests:
                        print("⚠️ レート制限に到達。15分待機")
                        time.sleep(15 * 60)  # 15分待機
                    except tweepy.TweepyException as e:
                        print(f"⚠️ リプライ送信エラー: {e}")

        else:
            print(f"⚠️ {target_user} の新しいリプライはなし。次のターゲットへ")

        # 次のターゲットに切り替え
        current_index = (current_index + 1) % len(TARGET_USER_IDS)

        # 16分待機
        print(f"⏳ 次の監視対象: {TARGET_USER_IDS[current_index]} (16分後)")
        time.sleep(16 * 60)

    except tweepy.TooManyRequests:
        print("⚠️ レート制限に到達。15分待機")
        time.sleep(15 * 60)  # 15分待機
    except requests.exceptions.RequestException as e:
        print(f"⚠️ ネットワークエラー発生: {e}. 30秒後にリトライ")
        time.sleep(30)  # 30秒待機して再試行
    except tweepy.TweepyException as e:
        print(f"⚠️ エラー発生: {e}")
        time.sleep(60)  # APIエラー時は1分待機
