# ChatGPTTwitchTranslator

## 説明

Twitch のチャットを自動で翻訳するボットプログラムです。日本語のコメントは英語に翻訳します、日本語以外のコメントは日本語に翻訳します。

翻訳には ChatGPT を使用し、コメントの履歴を考慮した翻訳を行います。


## インストール方法

```bash
pip install -r requirements.txt
```

## 使用方法

Twitch OAuth Password と OpenAI API Key を設定する必要があります。環境変数を設定するかソースコードを編集して設定してください。

```py
# 環境変数で設定する
TWITCH_CHAT_OAUTH_PASSWORD = os.getenv("TWITCH_CHAT_OAUTH_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```


```bash
python run.py --channel XXXX --send-message
```

--channel には翻訳をおこなうチャンネル名を指定してください。--send-message を指定すると翻訳結果がチャンネルに送信されますが、省いた場合は送信はされず翻訳結果だけをコンソールで確認できます。