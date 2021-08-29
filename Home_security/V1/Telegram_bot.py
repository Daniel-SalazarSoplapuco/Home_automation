from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram as t
import sys
import passwords as pw

class Telegram_bot(object):

    def __init__(self, input_token):
        self.bot = t.Bot(token=input_token)
        self.to_whom = "1514751302"

    def send_message(self, messsage="Hi, there!"):
        # on usage of this command, an message can be sent to any user regardless if there is an ongoing conversation
        self.bot.send_message(chat_id=self.to_whom, text=messsage)
        
    def send_image(self, path):
        self.bot.send_photo(chat_id=self.to_whom, photo=open(path, 'rb'))

if __name__ == "__main__":
    print(pw.telegram_pw())
    run = Telegram_bot()
    run.send_message()
    