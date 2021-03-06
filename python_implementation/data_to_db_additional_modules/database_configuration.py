"""
Configuring database, its shape and declaring possibly helpful functions to operate on it
"""

from peewee import *
from datetime import date
import os
import pytz
import datetime
import errno

PATH_TO_DB = "../appData/doNotSync/database.db"

# Ensuring that given path to db exists and database can be created there
if not os.path.exists(os.path.dirname(PATH_TO_DB)):
    try:
        os.makedirs(os.path.dirname(PATH_TO_DB))
    except OSError as exc:
        # makedirs will throw error if that path exists
        # for us it's ok, we can omit it, but let's make sure 
        # that OSError wasn't called for some other reason
        if exc.errno != errno.EEXIST:
            raise

# Deleting old db worked every time when file was imported
# TODO: Need to develop some way to run it conditionally
# try:
#     os.remove(PATH_TO_DB)
# except OSError:
#     print("Error: DB file cannot be removed")
#     pass

db = SqliteDatabase(PATH_TO_DB)

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    name = CharField(unique=True)

class Chat(BaseModel):
    name = CharField(unique=True)

class Message(BaseModel):
    text = CharField(null = True)
    created_by = ForeignKeyField(User)
    posted_in = ForeignKeyField(Chat)
    date_with_timezone = DateTimeField()
    date_utc = DateTimeField()
    external_media_path = CharField(null=True)

def createChat(chatName):
    thread = Chat.get_or_create(name=chatName)
    return thread[0].id

def findChat(chatName):
    return (Chat.get(Chat.name == chatName))

def createUser(userName):
    return User.get_or_create(name = userName)

def createMessage(messageText, userId, chatId, dateOfPosting, external_media):
    if external_media is None:
        external_media = ""
    utc_date = dateOfPosting.astimezone(pytz.utc)
    msg = Message.create(text=messageText, created_by = userId, posted_in = chatId, date_with_timezone=dateOfPosting, date_utc=utc_date, external_media_path = external_media)
    return msg.id

waiting_queue = []

def createMessage_AddLater(messageText, userId, chatId, dateOfPosting, external_media=""):
    if external_media is None:
        external_media = ""
    utc_date = dateOfPosting.astimezone(pytz.utc)
    utc_date = utc_date.replace(tzinfo=None)
    waiting_queue.append({'text':messageText, 'created_by': userId, 'posted_in': chatId, 'date_with_timezone': dateOfPosting, 'date_utc':utc_date, 'external_media_path': external_media })
    if len(waiting_queue) >= 100: # default max in bulk insert is 999 https://www.sqlite.org/limits.html#max_variable_number
        addAllFromWaitingQueue()

def addAllFromWaitingQueue():
    if len(waiting_queue) == 0:
        return
    try:
        Message.insert_many(waiting_queue).execute()
    except:
        pass
    waiting_queue.clear()

db.connect()
db.create_tables([User, Chat, Message], True)
