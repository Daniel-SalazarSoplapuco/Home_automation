import config
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
import sys

def telegram_test(input_token=config.telegram_pw(), user_id=config.telegram_admin_id(), message="Hi there"):
    tele_bot = t.Bot(token=input_token)
    tele_bot.send_message(chat_id=user_id, text=message)
    

class UserClass():

    def __init__(self, user_id):
        self.user_id = user_id
        self.authorized_commands = ["/auth", "/list_commands", "/stop"]
        self.admin = False
        self.tries = 0
        self.max_tries = 5
        
        self.banned = False
        self.ban_time = 30
        self.banned_at = dt.datetime.now()

    def is_authorized(self, command):
        return command in self.authorized_commands and not(self.banned)
    
    def add_commands(self, command):
        # provide user access to additional command
        if command not in self.authorized_commands:
            self.authorized_commands.append(command)

    def is_banned(self):
        # return the banned status of a user, unban if the ban time has been completed, also count of tries without admins tatus
        if self.banned and self.remaining_ban() <= 0:
            self.banned = False
            self.tries = 0
        elif not self.admin and self.tries > self.max_tries and not(self.banned):
            self.banned = True
            self.banned_at = dt.datetime.now()
        elif not self.admin:
            self.tries += 1
        return self.banned

    def remaining_ban(self):
        # return remaining ban time of user if banned
        return round(self.ban_time - (dt.datetime.now() - self.banned_at).total_seconds(), 0)

    def remove_rights(self):
        # ban and remove rights  
        self.admin = False
        self.authorized_commands = ["/auth", "/list_commands", "/stop"]

class TelegramBot(object):

    def __init__(self, bot_name, token, one_time_password, queue_object, psuedo_commands=None):
        self.auth_challenge = pyotp.TOTP(one_time_password)
        self.queue = queue_object
        self.thread = 'Telegram' 

        self.bot = t.Bot(token=token)
        self.update = Updater(bot=self.bot, use_context=True)
        
        # self.update = Updater(token, use_context=True)
        self.bot_name = bot_name
        self.dp = self.update.dispatcher
        self.users = {}
        # self.create_admin()

        # commands that will be available to the user
        self.command_dict = {'/stop': self.stop, '/auth': self.auth, "/list_commands": self.list_commands, '/terminate': self.terminate}

        # add psuedo commands to self.command_dict
        if psuedo_commands is not None:
            self.add_psuedo_commands(psuedo_commands)


        # add every key and command to the telegram command handler
        for key in self.command_dict:
            print(
                "init: add key '{}' with function '{}' to Command Handler".format(key, self.command_dict[key].__name__))
            self.dp.add_handler(CommandHandler(key[1:], self.universal_handler, pass_args=True))

    def run(self):
        self.update.start_polling()
        
    def universal_handler(self, update, context):
        update.message.text = update.message.text.split(' ')[0]
        self.report_to_queue(update, context.args)
        update = self.check_user(update)
        self.command_dict[update.message.text](update, context)

    def return_user(self, user_id):
        # get user object, if no user exists create one
        if user_id not in self.users:
            self.users[user_id] = UserClass(user_id)
        return self.users[user_id]

    def check_user(self, update):
        user = self.return_user(update.message.chat.id)
        if user.is_banned():
            self.reply_message(update, "You have been banned for '{}' seconds".format(user.remaining_ban()))
            update.message.text = "/stop"
        elif not user.is_authorized(update.message.text):
            self.reply_message(update, ("You don't have access to command: '{}'".format(update.message.text)))
            update.message.text = "/stop"
        return update

    def auth(self, update, context):
        verify_number = self.auth_challenge.now()
        user = self.return_user(update.message.chat.id)

        if not context.args:
            self.reply_message(update, "Please authenticate yourself \n Format: /auth XXXXXX")
        else:
            if not context.args[0] == str(verify_number):
                self.reply_message(update, "The provided password is incorrect")
            else:
                user.admin = True
                self.admin_assign_commands(user.user_id)
                self.reply_message(update, "You are now an admin")
                self.list_commands(update, context)
                self.one_admin(update)

    def admin_assign_commands(self, user_id):
        user = self.return_user(user_id)
        for key in list(self.command_dict.keys()):
            user.add_commands(key)


    def list_commands(self, update, context):
        user = self.return_user(update.message.chat.id)
        commands_available = ' '.join(map(str, user.authorized_commands))
        commands_available = commands_available.strip().replace(' ', ' \n')
        commands_available = 'The following commands are available to you: \n' + commands_available
        self.reply_message(update, commands_available)

    def report_to_queue(self, update, context):
        user = self.return_user(update.message.chat.id)

        if not user.is_authorized(update.message.text):
            context = None
        Message = "[Telegram]: user: [{}], who is admin [{}], requested command [{}] granted [{}]".format(
            user.user_id, user.admin, update.message.text, user.is_authorized(update.message.text)
        )
        Arguments = [user.is_authorized(update.message.text), user.user_id, user.admin, update.message.text, context,
                     dt.datetime.now().strftime("%Y%m%d %H:%M:%S")]
        self.queue.put([self.thread, Message, Arguments])

    def stop(self, update, context):
        pass
    
    def terminate(self, update=None, context=None):
        # -> add confirmation request from user as this would prevent any futher interaction between main and user
        # -> what to do if radar is still on and user has already terminated telegram?
        self.update.stop()
    
    def reply_message(self, update, message):
        update.message.reply_text(message)

    def send_message(self, to_whom, message):
        self.bot.send_message(chat_id=to_whom, text=message)

    def send_image(self, to_whom, path):
        self.bot.send_photo(chat_id=to_whom, photo=open(path, 'rb'))
        
    def send_video(self, to_whom, path):
        self.bot.send_video(chat_id=to_whom, video=open(path, 'rb'), supports_streaming=True)
        
    def send_file(self, to_whom, path):
        self.bot.send_document(chat_id=to_whom, document=open(path, 'rb'))    

    def one_admin(self, update):
        # ensure that only admin exists, dethrone all other admins if new admin appears
        # -> if 2 admins exist ask new admin to fill in auth twice?
        for key in self.users:
            user = self.return_user(key)
            if user.user_id != update.message.chat.id:
                user.remove_rights()
                self.send_message(update.message.chat.id, "You have been dethroned")

    def return_admin(self):
        for key in self.users:
            if self.users[key].admin:
                return self.users[key].user_id
    
    def add_psuedo_commands(self, command_list):
        if type(command_list) is list():
            command_list = [command_list]
        for command in command_list:
            if not command[0].startswith("/"):
                command = "/" + command
                
            self.command_dict[command] = self.stop
              
    def create_admin(self):
        self.users[config.telegram_admin_id()] = UserClass(config.telegram_admin_id())
        self.users[config.telegram_admin_id()].admin = True           
        self.admin_assign_commands(config.telegram_admin_id())

if __name__ == '__main__':

    q = Queue(maxsize=100)
    bot = TelegramBot("Home", config.telegram_pw(), config.one_time_password(), q, psuedo_commands=['/hello', '/idiot', '/test'])
    bot.create_admin()
    print(bot.return_admin())
    bot.send_image(config.telegram_admin_id(), "/home/uf829d/Projects/Raspberry_home_automation/Home_security/V3/program_files/Camera/Picture/output/image_2021-09-09_21-28-13.jpg")