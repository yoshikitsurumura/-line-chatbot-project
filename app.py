from flask import Flask, request, abort

from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)

import os
import sys
import random

# Render再デプロイ用のコメント

app = Flask(__name__)

# 環境変数からチャネルシークレットとチャネルアクセストークンを取得
channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
channel_access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text
    reply_text = ""

    # キーワード応答の辞書
    keyword_map = {
        "こんにちは": "こんにちは！",
        "ありがとう": "どういたしまして！",
        "使い方": "キーワードを送信すると、それに合わせた返信をします。「おみくじ」と送ってみてください。"
    }

    # 完全一致するキーワードを探す
    if user_message in keyword_map:
        reply_text = keyword_map[user_message]
    # 特別なキーワード「おみくじ」の処理
    elif user_message == "おみくじ":
        fortunes = ["大吉", "中吉", "小吉", "吉", "凶"]
        reply_text = f"今日の運勢は【{random.choice(fortunes)}】です！"
    # どのキーワードにも当てはまらない場合はオウム返し
    else:
        reply_text = user_message

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    # RenderなどのPaaSで実行する際は、環境変数PORTを利用する
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)