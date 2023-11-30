import argparse
#from datetime import datetime
#from enum import Enum, auto
import os
#import random
import signal

from openai import OpenAI
from twitchio import Channel, Message
from twitchio.ext import commands


DEFAULT_TWITCH_CHANNEL = "akiraaak"
TWITCH_CHAT_OAUTH_PASSWORD = os.getenv("TWITCH_CHAT_OAUTH_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHATGPT_MODEL = "gpt-4-1106-preview"
#CHATGPT_MODEL = "gpt-3.5-turbo-1106"
#CHATGPT_MODEL = "gpt-3.5-turbo"
# gpt-3.5-turbo-1106, gpt-4, gpt-4-1106-preview
COMMAND_PREFIX = "!"
#TRANSLATE_FROM_LANGUAGE = "日本語"
#TRANSLATE_FROM_LANGUAGE = "英語"
#TRANSLATE_TO_LANGUAGE = "英語"
TRANSLATE_LANGUAGE = "日本語"
TRANSLATE_LANGUAGE_TAG = "ja"
NONE_TAG = "#NONE#"

def translate(username: str, message: str, message_history: list[str]) -> str:
    message_history_text = '\n'.join(message_history)
    SYSTEM_MESSAGE = f"""あなたは投稿されたメッセージを{TRANSLATE_LANGUAGE}に翻訳するボットです。
しかし、投稿されたメッセージが{TRANSLATE_LANGUAGE}であれば{NONE_TAG}と返してください。
メッセージは `[ユーザー名]:[メッセージ]` の形式で投稿されていますが、メッセージのみを翻訳してください。
翻訳できない場合は{NONE_TAG}と返し、その後ろに理由も付けてください。
過去のメッセージの履歴が存在する場合はそれも考慮して翻訳してください。
==== 過去のメッセージの履歴 ====
{message_history_text}
==== 過去のメッセージの履歴ここまで ====
"""

    user_content = f"""{message}"""

    client = OpenAI(
        api_key=OPENAI_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_MESSAGE,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        model=CHATGPT_MODEL,
    )
    #print("---- SYSTEM ----")
    #print(SYSTEM_MESSAGE)
    #print("---- END SYSTEM ----")
    #print("---- USER ----")
    #print(user_content)
    #print("---- END USER ----")
    translated_message = chat_completion.choices[0].message.content
    return translated_message


class Bot(commands.Bot):
    MAX_MESSAGE_HISTORY = 20

    def __init__(self, channel: str):
        super().__init__(
            token=TWITCH_CHAT_OAUTH_PASSWORD, prefix=COMMAND_PREFIX, initial_channels=[channel]
        )
        self.message_history = []

    async def event_channel_joined(self, channel: Channel):
        print("---- event_channel_joined ----")
        print(f"チャンネル名: {channel.name}\n")

    async def event_ready(self):
        print("---- event_ready ----")
        print("全てのチャンネルにログインしました。")
        print(f'ユーザーID: {self.user_id}')
        print(f'ユーザー名: {self.nick}\n')

    async def event_message(self, message: Message):
        # ボットの発言は無視する
        if message.echo:
            return

        # メッセージがコマンドであれば、ここで処理を終了
        if message.content.startswith(COMMAND_PREFIX):
            return

        if message.author.display_name != message.author.name:
            formated_user_name = f"{message.author.display_name}({message.author.name})"
        else:
            formated_user_name = message.author.name

        formated_message_line = f"{formated_user_name}: {message.content}"
        translated_message = translate(username=formated_user_name, message=message.content, message_history=self.message_history)

        print(f"{formated_user_name}: {message.content}")
        self.message_history.append(formated_message_line)

        print(f"translated_message: >{TRANSLATE_LANGUAGE_TAG} {translated_message} \n")
 
        self.message_history = self.message_history[-self.MAX_MESSAGE_HISTORY:]

        if NONE_TAG not in translated_message:
            # await message.channel.send(f"/me {message_text}")
            print("!!!!!!!!!!!!!!!!!SEND MESSAGE!!!!!!!!!!!!!!!!!")


def main():
    parser = argparse.ArgumentParser(description="TwitchTranslator")
    parser.add_argument(
        "--channel", type=str, default=DEFAULT_TWITCH_CHANNEL, help="入室するチャンネル名"
    )
    args = parser.parse_args()

    bot = Bot(channel=args.channel)
    bot.run()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
