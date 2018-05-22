# -*- coding: utf-8 -*-
"""
SQLite Database Helper


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import os
from datetime import datetime

from peewee import *
import utils

# The database should be initialized from runtime config
database = SqliteDatabase(None)

def set_path(path):
    database.init(path)
    db_integrity_check()

class BaseModel(Model):

    class Meta:
        database = database


class History(BaseModel):
    historyid = PrimaryKeyField(db_column='historyID')
    historydate = DateTimeField(db_column='historyDate')
    historytext = CharField(db_column='historyText')
    historytypeid = IntegerField(db_column='historyTypeID')
    vidid = IntegerField(db_column='vidID')

    class Meta:
        db_table = 'history'


class Historytypes(BaseModel):
    historytypeid = PrimaryKeyField(db_column='historyTypeID')
    historytype = CharField(db_column='historyType')

    class Meta:
        db_table = 'historyTypes'


class Videos(BaseModel):
    vidid = PrimaryKeyField(db_column='vidID')
    vidname = CharField()
    vidtype = CharField()
    titleindex = CharField(db_column='titleIndex')
    path = CharField()
    filename = CharField(null=True)
    filebot = BooleanField()
    statusid = IntegerField(db_column='statusID')
    lastupdated = DateTimeField(db_column='lastUpdated')

    class Meta:
        db_table = 'videos'


class Statustypes(BaseModel):
    statusid = PrimaryKeyField(db_column='statusID')
    statustext = CharField(db_column='statusText')

    class Meta:
        db_table = 'statusTypes'


def create_tables():
    database.connect()

    # Fail silently if tables exists
    History.create_table(True)
    Historytypes.create_table(True)
    Videos.create_table(True)
    Statustypes.create_table(True)


def create_history_types():
    historytypes = [
        [1, 'Info'],
        [2, 'Error'],
        [3, 'MakeMKV Error'],
        [4, 'Handbrake Error']
    ]

    c = 0
    for z in Historytypes.select():
        c += 1

    if c != len(historytypes):
        for hID, hType in historytypes:
            Historytypes.create(historytypeid=hID, historytype=hType)

def create_status_types():
    statustypes = [
        [1, 'Added'],
        [2, 'Error'],
        [3, 'Submitted to makeMKV'],
        [4, 'Awaiting HandBrake'],
        [5, 'Submitted to HandBrake'],
        [6, 'Awaiting FileBot'],
        [7, 'Submitted to FileBot'],
        [8, 'Completed']
    ]

    c = 0
    for z in Statustypes.select():
        c += 1

    if c != len(statustypes):
        for sID, sType in statustypes:
            Statustypes.create(statusid=sID, statustext=sType)


def next_video_to_compress():
    videos = Videos.select().where((Videos.statusid == 4) & (
        Videos.filename != "None")).order_by(Videos.vidname)
    return videos


def next_video_to_filebot():
    videos = Videos.select().where((Videos.statusid == 6) & (
        Videos.filename != "None") & (Videos.filebot == 1))
    return videos

def search_video_name(invid):
    vidqty = Videos.select().where(Videos.filename.startswith(invid)).count()
    return vidqty


def insert_history(dbvideo, text, typeid=1):
    return History.create(
        vidid=dbvideo.vidid,
        historytext=text,
        historydate=datetime.now(),
        historytypeid=typeid
    )


def insert_video(title, path, vidtype, index, filebot):
    return Videos.create(
        vidname=title,
        vidtype=vidtype,
        titleindex=index,
        path=path,
        filename="None",
        filebot=filebot,
        statusid=1,
        lastupdated=datetime.now()
    )


def update_video(vidobj, statusid, filename=None):
    vidobj.statusid = statusid
    vidobj.lastupdated = datetime.now()

    if filename is not None:
        filename = utils.strip_accents(filename)
        filename = utils.clean_special_chars(filename)
        vidobj.filename = filename

    vidobj.save()

# Must be called after database is initialized
def db_integrity_check():
    # Stuff
    create_tables()

    # Things
    create_history_types()
    create_status_types()
