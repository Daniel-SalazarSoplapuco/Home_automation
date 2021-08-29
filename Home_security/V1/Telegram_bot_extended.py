import passwords as pw
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import telegram as t
import subprocess
import re
import pyotp
import random
import datetime as dt
import time as tm
import json
import pickle
from queue import Queue

class UserClass(object):

    def __init__(self, user_id):
        self.user_id = user_id
        self.authorized_commands = ["/auth", "/list_commands", "/stop"]
        self.admin = False
        self.tries = 0
        self.max_tries = 5
        self.banned_time = 30
        self.banned_at = dt.datetime.now()
        self.status = "free"

    def banned(self):
        if self.status == "Banned":
            if (dt.datetime.now() - self.banned_at).total_seconds() > self.banned_time:
                self.status = "free"
                self.tries = 0
            else:
                return True
        elif not self.admin:
            self.tries += 1
            if self.tries > self.max_tries:
                self.status = "Banned"
                self.banned_at = dt.datetime.now()
                return True
        return False

    def ban_time(self):
        return round(self.banned_time - (dt.datetime.now() - self.banned_at).total_seconds(), 0)

    def add_commands(self, command):
        if command not in self.authorized_commands:
            self.authorized_commands.append(command)

    def command_granted(self, command):
        if command in self.authorized_commands and self.status != "Banned":
            return True
        else:
            return False

    def dethrone(self):
        self.status = "Banned"
        self.admin = False

class TelegramBot(object):

    def __init__(self, bot_name, token, one_time_password, q):
        self.auth_challenge = pyotp.TOTP(one_time_password)
        self.queue = q


        self.bot = t.Bot(token=token)
        self.update = Updater(bot=self.bot, use_context=True)
        # self.update = Updater(token, use_context=True)
        self.bot_name = bot_name

        self.dp = self.update.dispatcher
        self.users = {}
        self.create_admin()

        # commands that will be available to the user
        self.command_dict = {'/stop': self.stop, '/auth': self.auth, '/picture': self.picture,
                             "/arm_security": self.arm_security, "/disarm_security": self.disarm_security,
                             "/list_commands": self.list_commands, "/video": self.video, '/status': self.status, '/start_return_feed': self.start_return_feed, '/stop_return_feed': self.stop_return_feed,
                             '/shutdown': self.shutdown}

        # add every key and command to the telegram command handler
        for key in self.command_dict:
            print(
                "init: add key '{}' with function '{}' to Command Handler".format(key, self.command_dict[key].__name__))
            self.dp.add_handler(CommandHandler(key[1:], self.universal_handler, pass_args=True))

        # start up program
        self.run()

    def run(self):
        self.update.start_polling()

    def universal_handler(self, update, context):
        update.message.text = update.message.text.split(' ')[0]
        self.report_to_queue(update)
        update = self.check_user(update)
        print("Handler: user command: {} ".format(update.message.text))
        self.command_dict[update.message.text](update, context)

    def return_user(self, update):
        if type(update) is str:
            user_id = update
        else:
            user_id = update.message.chat.id
        if user_id in self.users:
            return self.users[user_id]
        else:
            self.users[user_id] = UserClass(user_id)
            return self.users[user_id]

    def check_user(self, update):
        user = self.return_user(update)
        if user.banned():
            self.message(update, "You have been banned for '{}' seconds".format(user.ban_time()))
            update.message.text = "/stop"
        elif not user.command_granted(update.message.text):
            self.message(update, ("You don't have access to command: '{}'".format(update.message.text)))
            update.message.text = "/stop"
        return update

    def auth(self, update, context):
        verify_number = self.auth_challenge.now()
        user = self.return_user(update)

        if not context.args:
            self.message(update, "Please authenticate yourself \n Format: /auth XXXXXX")
        else:
            if not context.args[0] == str(verify_number):
                self.message(update, "The provided password is incorrect")
            else:
                user.admin = True
                for key in list(self.command_dict.keys()):
                    user.add_commands(key)
                self.message(update, "You are now an admin")
                self.list_commands(update, context)
                self.one_admin(update)

    def list_commands(self, update, context):
        user = self.return_user(update)
        commands_available = ' '.join(map(str, user.authorized_commands))
        commands_available = commands_available.strip().replace(' ', ' \n')
        commands_available = 'The following commands are available to you: \n' + commands_available
        self.message(update, commands_available)

    def report_to_queue(self, update):
        user = self.return_user(update)
        Thread = "Telegram"
        Message = "[Telegram]: user: [{}], who is admin [{}], requested command [{}] granted [{}]".format(
            user.user_id, user.admin, update.message.text, user.command_granted(update.message.text)
        )
        Arguments = [user.user_id, user.admin, update.message.text, user.command_granted(update.message.text),
                     dt.datetime.now().strftime("%Y%m%d %H:%M:%S")]
        self.queue.put([Thread, Message, Arguments])

    def picture(self, update, context):
        pass

    def video(self, update, context):
        pass
    
    def gif(self, update, context):
        pass
    
    def arm_security(self, update, context):
        pass

    def disarm_security(self, update, context):
        pass
    
    def start_return_feed(self, update, context):
        pass
    
    def stop_return_feed(self, update, context):
        pass
        
    def status(self, update, context):
        pass
    
    def shutdown(self, update, context):
        pass
    
    def message(self, update, message):
        update.message.reply_text(message)

    def stop(self, update, context):
        pass

    def send_message(self, to_whom, message):
        self.bot.send_message(chat_id=to_whom, text=message)

    def send_image(self, to_whom, path):
        self.bot.send_photo(chat_id=to_whom, photo=open(path, 'rb'))
        
    def send_video(self, to_whom, path):
        self.bot.send_video(chat_id=to_whom, video=open(path, 'rb'), supports_streaming=True)
        
    def send_file(self, to_whom, path):
        self.bot.send_document(chat_id=to_whom, document=open(path, 'rb'))

    def one_admin(self, update):
        for key in self.users:
            user = self.return_user(str(key))
            if user.user_id != update.message.chat.id:
                user.dethrone()
                self.send_message(update.message.chat.id, "You have been dethroned")

    def return_admin(self):
        for key in self.users:
            if self.users[key].admin:
                return self.users[key].user_id

    def create_admin(self):
        self.users["1514751302"] = UserClass("1514751302")
        self.users["1514751302"].admin = True

if __name__ == '__main__':
    q = Queue(maxsize=100)
    bot = TelegramBot("zerow", pw.telegram_pw(), pw.one_time_password(), q)
    print(bot.return_admin())
