import tweepy
import openai
import os
import time
import requests

# ==== SECRETS ====
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ==== TWITTER AUTH ====
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# ==== TRACKED USERS ====
USERS = {
    'elonmusk': '44196397',
    'TrumpDailyPosts': '1365057771372974082'
}
last_seen_ids = {user: None for user in USERS}

# ==== OPENAI-GENERATED COMMENT ====
def generate_reply(tweet_text):
    prompt = f"""
You are a cynical stand-up comedian with a dark sense of humor. You just saw this tweet:

"{tweet_text}"

Now deliver a short, sharp roast. Don’t explain anything. Just make it funny, absurd, brutally honest, and weirdly accurate. Keep it under 280 characters. No hashtags. No emojis.
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT Error: {e}"

# ==== DISCORD NOTIFICATION ====
def send_discord_notification(username, tweet_text, roast, tweet_url):
    if not DISCORD_WEBHOOK_URL:
        print("❌ No Discord webhook configured.")
        return

    message = f'{username}: "{tweet_text}"\n\n"{roast}"\n\n{tweet_url}'
    payload = {"content": message}
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("📣 Discord notification sent.")
    except Exception as e:
        print(f"❌ Error sending Discord message: {e}")

# ==== CHECK USER POSTS ====
def check_user(username, user_id):
    global last_seen_ids
    try:
        tweets = client.get_users_tweets(id=user_id, max_results=10, tweet_fields=["created_at"])
    except Exception as e:
        print(f"❌ Error fetching tweets from {username}: {e}")
        return

    if tweets.data:
        tweet = tweets.data[0]
        if tweet.id != last_seen_ids[username]:
            last_seen_ids[username] = tweet.id
            tweet_url = f"https://twitter.com/{username}/status/{tweet.id}"
            roast = generate_reply(tweet.text)

            print(f"\n🧠 {username} just posted:")
            print(f"“{tweet.text}”\n")
            print(f"{roast}\n{tweet_url}")
            print("-" * 70)

            send_discord_notification(username, tweet.text, roast, tweet_url)

# ==== MAIN LOOP ====
while True:
    for username, user_id in USERS.items():
        check_user(username, user_id)
    time.sleep(300)  # Check every 5 minutes
