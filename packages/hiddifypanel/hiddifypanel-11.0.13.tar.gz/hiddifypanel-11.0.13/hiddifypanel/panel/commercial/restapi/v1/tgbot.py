import telebot
from flask import request
from apiflask import abort
from flask_restful import Resource
import time

from hiddifypanel.models import *
from hiddifypanel import Events
from hiddifypanel.cache import cache
logger = telebot.logger


class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        """Improved error handling for Telegram bot exceptions"""
        error_msg = str(exception)
        logger.error(f"Telegram bot error: {error_msg}")
        
        try:
            # Attempt recovery based on error type
            if "webhook" in error_msg.lower():
                if hasattr(bot, 'remove_webhook'):
                    bot.remove_webhook()
                    logger.info("Removed webhook due to error")
            elif "connection" in error_msg.lower():
                # Wait and retry for connection issues
                time.sleep(5)
                return True  # Indicates retry
        except Exception as e:
            logger.error(f"Error during recovery attempt: {str(e)}")
        
        return False  # Don't retry for unknown errors


bot = telebot.TeleBot("1:2", parse_mode="HTML", threaded=False, exception_handler=ExceptionHandler())
bot.username = ''


@cache.cache(1000)
def register_bot_cached(set_hook=False, remove_hook=False):
    return register_bot(set_hook, remove_hook)


def register_bot(set_hook=False, remove_hook=False):
    try:
        global bot
        token = hconfig(ConfigEnum.telegram_bot_token)
        if token:
            bot.token = hconfig(ConfigEnum.telegram_bot_token)
            try:
                bot.username = bot.get_me().username
            except BaseException:
                pass
            if remove_hook:
                bot.remove_webhook()
            domain = Domain.get_panel_link()
            if not domain:
                raise Exception('Cannot get valid domain for setting telegram bot webhook')

            admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin)

            user_secret = AdminUser.get_super_admin_uuid()
            if set_hook:
                bot.set_webhook(url=f"https://{domain}/{admin_proxy_path}/{user_secret}/api/v1/tgbot/")
    except Exception as e:
        logger.error(e)
        


def init_app(app):
    with app.app_context():
        global bot
        token = hconfig(ConfigEnum.telegram_bot_token)
        if token:
            bot.token = token
            try:
                bot.username = bot.get_me().username
            except BaseException:
                pass


class TGBotResource(Resource):
    def post(self):
        try:
            if request.headers.get('content-type') == 'application/json':
                json_string = request.get_data().decode('utf-8')
                update = telebot.types.Update.de_json(json_string)
                bot.process_new_updates([update])
                return ''
            else:
                abort(403)
        except Exception as e:
            print("Error", e)
            import traceback
            traceback.print_exc()
            return "", 500
