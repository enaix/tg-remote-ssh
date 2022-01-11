#!/usr/bin/env python3

from telegram import Update, ForceReply, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import escape_markdown

import os
import subprocess
import threading
import json
import time

class CBot():
    def __init__(self):
        self.working_dir = os.getcwd()
        self.load_config()
        self.users_count = 0
        self.init_timer()
        self.web_addr = None
        self.allow = set(self.bot_set["admins"]) & set(self.bot_set["allowed_ssh_ids"]) &\
                set(self.bot_set["allowed_web_ids"]) & set(self.bot_set["allowed_webtoken_ids"])
        self.user_greet = 'Hello, {user}! Your account has been logged on the server. Please login and whitelist your user ID.'
    
        self.updater = Updater(self.bot_env["token"])
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("ssh", self.ssh))
        self.dispatcher.add_handler(CommandHandler("web", self.address))
        self.dispatcher.add_handler(CommandHandler("webtoken", self.get_web_token))
        self.dispatcher.add_handler(MessageHandler(Filters.document, self.fetch_file))
        
    def load_env(self, filename):
        with open(filename, 'r') as f:
            self.bot_env = json.load(f)

    def load_settings(self, filename):
        with open(filename, 'r') as f:
            self.bot_set = json.load(f)

    def load_config(self):
        self.load_env(os.path.join(self.working_dir, "env"))
        self.load_settings(os.path.join(self.working_dir, "settings"))

    def upd_users(self):
        self.users_count = 0
        self.init_timer()

    def init_timer(self):
        t = threading.Timer(self.bot_set["spam_interval"], self.upd_users)
        t.start()

    def enable_logging(self):
        self.bot_set["enable_logging"] = True
        self.users_count = 0

    def check_spam(self, context: CallbackContext):
        if self.bot_set["enable_logging"]:
            if self.users_count < self.bot_set["spam_threshold"]:
                return False
            else:
                for u in self.bot_set["admins"]:
                    context.bot.send_message(chat_id=u, text="Warning! The spam attack has been detected. The new users logging will be reenabled in "\
                            + str(self.bot_set["spam_cooldown"]) + " seconds.")
                self.bot_set["enable_logging"] = False
                t = threading.Timer(self.bot_set["spam_cooldown"], self.enable_logging)
                t.start()
                return True

    def check_and_log(self, user, ctx, notify=True):
        self.users_count += 1
        if not self.check_spam(ctx):
            with open(os.path.join(self.working_dir, "users_log"), 'a') as f:
                f.write(time.strftime("%a %d %b %H:%M:%S", time.localtime()) + ' ' + str(user) + '\n')
            if notify and self.bot_set["notify_on_login"]:
                for u in self.bot_set["admins"]:
                    ctx.bot.send_message(chat_id=u, text="New login attempt: user "\
                            + str(user["id"]) + " (" + str(user["first_name"]) + " " + str(user["last_name"]) + ")")
            return True
        return False

    def start(self, update: Update, context: CallbackContext) -> None:
        user = update.effective_user
        if user.id in self.allow:
            update.message.reply_markdown_v2(
                esc(fr'Welcome back, {user["first_name"]}!'))
        else:
            if self.check_and_log(update.effective_user, context):
                update.message.reply_markdown_v2(esc(self.user_greet.format(user=user.mention_markdown_v2())))

    def run_cmd(self, cmd, *args):
        try:
            out = subprocess.check_output([os.path.abspath(cmd), *args],\
                    cwd=os.path.abspath(os.path.dirname(cmd)))
        except subprocess.CalledProcessError as err:
            return err
        return out

    def ssh(self, update: Update, context: CallbackContext) -> None:
        if not self.bot_set["enable_ssh"]:
            return
        user = update.effective_user
        if user.id in self.bot_set["allowed_ssh_ids"]:
            ssh_out = self.run_cmd(self.bot_set["ssh_script_path"])
            cmd = str(ssh_out.decode()).strip()
            if cmd == "":
                update.message.reply_markdown_v2(esc("SSH service not running"))
            else:
                update.message.reply_markdown_v2(esc(str("`") +  + str("`")))
        else:
            print("Access denied:", user)
            self.check_and_log(update.effective_user, context, notify=False)

    def address(self, update: Update, context: CallbackContext) -> None:
        if not self.bot_set["enable_server"]:
            return
        user = update.effective_user
        if user.id in self.bot_set["allowed_web_ids"]:
            web_out = self.run_cmd(self.bot_set["web_script_path"])
            self.web_addr = str(web_out.decode()).strip()
            update.message.reply_markdown_v2(esc("Webserver address: " + "https://" + self.web_addr))
        else:
            print("Access denied:", user)
            self.check_and_log(update.effective_user, context, notify=False)

    def get_web_token(self, update: Update, context: CallbackContext) -> None:
        if not self.bot_set["enable_webtoken"]:
            return
        user = update.effective_user
        if user.id in self.bot_set["allowed_webtoken_ids"]:
            token = self.run_cmd(self.bot_set["webtoken_script_path"])
            if self.bot_set["glue_webtoken"] and self.web_addr is not None:
                update.message.reply_markdown_v2(esc("Webserver address: " + "https://" + self.web_addr\
                        + "/?token=" + str(token.decode()).strip()))
            else:
                update.message.reply_markdown_v2(esc("Webserver token: " + "https://" + str(token.decode()).strip()))
        else:
            print("Access denied:", user)
            self.check_and_log(update.effective_user, context, notify=False)

    def fetch_file(self, update: Update, context: CallbackContext) -> None:
        if not self.bot_set["receive_files"]:
            return
        user = update.effective_user
        if user.id in self.bot_set["allowed_files_ids"]:
            filename = update.message.document.file_name
            if filename is None:
                filename = update.message.document.file_id + "." + update.message.document.mime_type
            out = "".join(x for x in filename if x.isalnum() or x in "._-")
            out_path = os.path.join(self.bot_set["files_save_folder"], out)
            if os.path.exists(out_path):
                dot_split = out.split(".")
                out_path = os.path.join(self.bot_set["files_save_folder"], ".".join(dot_split[:-1]) + "_" +\
                        update.message.document.file_id + "." + dot_split[len(dot_split)-1])
            with open(out_path, 'wb') as f:
                context.bot.get_file(update.message.document).download(out=f)
            update.message.reply_markdown_v2(esc("File saved as " + out_path))
        else:
            print("Access denied:", user)
            self.check_and_log(update.effective_user, context, notify=False)

def esc(text):
    return escape_markdown(text, version=2)

def main():
    bot = CBot()
    bot.updater.start_polling()
    bot.updater.idle()

if __name__ == '__main__':
    main()


