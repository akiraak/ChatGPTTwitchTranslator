import argparse
import json
import os
import signal

from openai import OpenAI
from twitchio import Channel, Message
from twitchio.ext import commands


# 環境変数で設定する
TWITCH_CHAT_OAUTH_PASSWORD = os.getenv("TWITCH_CHAT_OAUTH_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CHATGPT_MODEL = "gpt-4-1106-preview"
COMMAND_PREFIX = "!"


# ChatGPT API を叩く
def fetch_chatgpt(user_content: str, system_content: str = None) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)

    messages = [{"role": "user", "content": user_content}]
    if system_content is not None:
        messages.append({"role": "system", "content": system_content})

    response = client.chat.completions.create(
        messages=messages,
        model=CHATGPT_MODEL,
    )
    return response.choices[0].message.content


# メッセージを指定の言語で翻訳する
def translate_language(language: str, message: str, message_history: list[str]) -> (bool, str):
    NONE_TAG = "#NONE#"

    message_history_text = '\n'.join(message_history)
    system_content = f"""あなたは投稿されたメッセージを{language}に翻訳するボットです。
メッセージは `[ユーザー名]:[メッセージ]` の形式で投稿されていますが、メッセージのみを翻訳してください。
翻訳できない場合は{NONE_TAG}と返してください。
過去のメッセージの履歴が存在する場合はそれも考慮して翻訳してください。
==== 過去のメッセージの履歴 ====
{message_history_text}
==== 過去のメッセージの履歴ここまで ====
"""

    user_content = f"{message}"

    translated_message = fetch_chatgpt(user_content=user_content, system_content=system_content)
    if NONE_TAG in translated_message:
        return False, ""

    return True, translated_message


# メッセージを英語に翻訳する
def translate_english(message: str, message_history: list[str]) -> (bool, str):
    return translate_language(language="英語", message=message, message_history=message_history)


# メッセージを日本語に翻訳する
def translate_japanese(message: str, message_history: list[str]) -> (bool, str):
    return translate_language(language="日本語", message=message, message_history=message_history)


# メッセージが日本語かどうか判定する
def is_japanese(message: str) -> bool:
    JAPANESE_TAG = "ja"
    OTHERS_TAG = "others"

    system_content = f"""You are an AI designed to identify the language of a text.
If the input text is in Japanese, please return {JAPANESE_TAG}.
For languages other than Japanese, please return {OTHERS_TAG}."""

    user_content = f"{message}"

    language = fetch_chatgpt(system_content=system_content, user_content=user_content)

    return JAPANESE_TAG in language


# Twitch のチャットボット
class Bot(commands.Bot):
    MAX_MESSAGE_HISTORY = 20 # 過去のメッセージの履歴の最大数

    # 初期化＆ログイン
    def __init__(self, channel: str):
        super().__init__(
            token=TWITCH_CHAT_OAUTH_PASSWORD, prefix=COMMAND_PREFIX, initial_channels=[channel]
        )
        self.message_history = []

    # ログイン完了時の処理
    async def event_channel_joined(self, channel: Channel):
        print("---- event_channel_joined ----")
        print(f"チャンネル名: {channel.name}\n")

    # メッセージ受信時の処理
    async def event_message(self, message: Message):
        # ボットの発言は無視する
        if message.echo:
            return

        # メッセージがコマンドであれば処理を終了
        if message.content.startswith(COMMAND_PREFIX):
            return

        # ユーザー名の表示を整える
        if message.author.display_name != message.author.name:
            formated_user_name = f"{message.author.display_name}({message.author.name})"
        else:
            formated_user_name = message.author.name

        # メッセージ全体の表示を整える
        formated_message_line = f"{formated_user_name}: {message.content}"

        # メッセージが日本語かどうか判定する
        is_message_japanese = is_japanese(message=message.content)

        print(f"{formated_user_name}: {message.content}")
        if is_message_japanese:
            # 日本語の場合は英語に翻訳する
            success, translated_to_english_message = translate_english(message=formated_message_line, message_history=self.message_history)
            if success:
                print(f"{formated_user_name}: EN> {translated_to_english_message}\n")
            else:
                print("\n")
        else:
            # 日本語以外の場合は日本語に翻訳する    
            success, translated_to_japanese_message = translate_japanese(message=formated_message_line, message_history=self.message_history)
            if success:
                print(f"{formated_user_name}: JA> {translated_to_japanese_message}\n")
            else:
                print("\n")

        # メッセージの履歴をためる
        self.message_history.append(formated_message_line)
        self.message_history = self.message_history[-self.MAX_MESSAGE_HISTORY:]

        #if NONE_TAG not in translated_message:
        #    # await message.channel.send(f"/me {message_text}")
        #    print("!!!!!!!!!!!!!!!!!SEND MESSAGE!!!!!!!!!!!!!!!!!")


def main():
    parser = argparse.ArgumentParser(description="TwitchTranslator")
    parser.add_argument(
        "--channel", type=str, required=True, help="入室するチャンネル名"
    )
    args = parser.parse_args()

    bot = Bot(channel=args.channel)
    bot.run()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
