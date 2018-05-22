# -*- coding: utf-8 -*-
"""
Autorippr

Ripping
    Uses MakeMKV to watch for videos inserted into DVD/BD Drives

    Automaticly checks for existing directory/video and will NOT overwrite existing
    files or folders

    Checks minimum length of video to ensure video is ripped not previews or other
    junk that happens to be on the DVD

    DVD goes in > MakeMKV gets a proper DVD name > MakeMKV Rips

Compressing
    An optional additional used to rename and compress videos to an acceptable standard
    which still delivers quality audio and video but reduces the file size
    dramatically.

    Using a nice value of 15 by default, it runs HandBrake (or FFmpeg) as a background task
    that allows other critical tasks to complete first.

Extras


Released under the MIT license
Copyright (c) 2014, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT

Usage:
    autorippr.py   ( --rip | --compress | --extra )  [options]
    autorippr.py   ( --rip [ --compress ] )          [options]
    autorippr.py   --all                             [options]
    autorippr.py   --test

Options:
    -h --help           Show this screen.
    --version           Show version.
    --debug             Output debug.
    --rip               Rip disc using makeMKV.
    --compress          Compress using HandBrake or FFmpeg.
    --extra             Lookup, rename and/or download extras.
    --all               Do everything.
    --test              Tests config and requirements.
    --silent            Silent mode.
    --skip-compress     Skip the compression step.
    --force_db=(tv|movie)     Force use of the TheTVDB or TheMovieDB

"""

import errno
import os
import subprocess
import sys

import yaml
from classes import *
from tendo import singleton

__version__ = "1.7.0"

me = singleton.SingleInstance()
CONFIG_FILE = "{}/settings.cfg".format(
    os.path.dirname(os.path.abspath(__file__)))

notify = None


def eject(config, drive):
    """
        Ejects the DVD drive
        Not really worth its own class
    """
    log = logger.Logger("Eject", config['debug'], config['silent'])

    log.debug("Ejecting drive: " + drive)
    log.debug("Attempting OS detection")

    try:
        if sys.platform == 'win32':
            log.debug("OS detected as Windows")
            import ctypes
            ctypes.windll.winmm.mciSendStringW(
                "set cdaudio door open", None, drive, None)

        elif sys.platform == 'darwin':
            log.debug("OS detected as OSX")
            p = os.popen("drutil eject " + drive)

            while 1:
                line = p.readline()
                if not line:
                    break
                log.debug(line.strip())

        else:
            log.debug("OS detected as Unix")
            p = os.popen("eject -vm " + drive)

            while 1:
                line = p.readline()
                if not line:
                    break
                log.debug(line.strip())

    except Exception as ex:
        log.error("Could not detect OS or eject CD tray")
        log.ex("An exception of type {} occured.".format(type(ex).__name__))
        log.ex("Args: \r\n {}".format(ex.args))

    finally:
        del log


def rip(config):
    """
        Main function for ripping
        Does everything
        Returns nothing
    """
    log = logger.Logger("Rip", config['debug'], config['silent'])

    mkv_save_path = os.path.join(config['workDir'], 'raw')

    log.info("Ripping initialised")
    mkv_api = makemkv.MakeMKV(config)

    log.debug("Checking for DVDs")
    dvds = mkv_api.find_disc()

    log.debug("{} DVD(s) found".format(len(dvds)))

    if len(dvds) == 0:
        log.info("Could not find any DVDs in drive list")
        return

    # Best naming convention ever
    for dvd in dvds:
        mkv_api.set_title(dvd["discTitle"])
        mkv_api.set_index(dvd["discIndex"])

        disc_title = mkv_api.get_title()
        
        if not config['force_db']:
            disc_type = mkv_api.get_type()
        else:
            disc_type = config['force_db']

        disc_path = os.path.join(mkv_save_path, disc_title)
        if os.path.exists(disc_path):
            log.info("Video folder {} already exists".format(disc_title))
            continue

        os.makedirs(disc_path)

        mkv_api.get_disc_info()

        saveFiles = mkv_api.get_savefiles()

        if len(saveFiles) == 0:
            log.info("No video titles found")
            log.info("Try decreasing 'minLength' in the config and try again")
            continue

        filebot = config['filebot']['enable']

        for dvdTitle in saveFiles:

            dbvideo = database.insert_video(
                disc_title,
                disc_path,
                disc_type,
                dvdTitle['index'],
                filebot
            )

            database.insert_history(
                dbvideo,
                "Video added to database"
            )

            database.update_video(
                dbvideo,
                3,
                dvdTitle['title']
            )

            log.info("Attempting to rip {} from {}".format(
                dvdTitle['title'],
                disc_title
            ))

            if 'rip' in config['notification']['notify_on_state']:
                notify.rip_started(dbvideo)

            with stopwatch.StopWatch() as t:
                database.insert_history(
                    dbvideo,
                    "Video submitted to MakeMKV"
                )
                status = mkv_api.rip_disc(
                    mkv_save_path, dvdTitle['index'])

                # Master_and_Commander_De_l'autre_côté_du_monde_t00.mkv become
                # Master_and_Commander_De_l_autre_cote_du_monde_t00.mkv
                log.debug('Rename {} to {}'.format(
                    os.path.join(dbvideo.path, dvdTitle['title']),
                    os.path.join(dbvideo.path, dvdTitle['rename_title'])
                ))
                os.rename(
                    os.path.join(dbvideo.path, dvdTitle['title']),
                    os.path.join(dbvideo.path, dvdTitle['rename_title'])
                )

            if status:
                log.info("It took {} minute(s) to complete the ripping of {} from {}".format(
                    t.minutes,
                    dvdTitle['title'],
                    disc_title
                ))

                database.update_video(dbvideo, 4)

                if 'rip' in config['notification']['notify_on_state']:
                    notify.rip_complete(dbvideo, t.minutes)

            else:
                database.update_video(dbvideo, 2)

                database.insert_history(
                    dbvideo,
                    "MakeMKV failed to rip video"
                )
                notify.rip_fail(dbvideo)

                log.info(
                    "MakeMKV did not did not complete successfully")
                log.info("See log for more details")

        if config['makemkv']['eject']:
            eject(config, dvd['location'])

def skip_compress(config):
    """
        Main function for skipping compression
        Does everything
        Returns nothing
    """
    log = logger.Logger("Skip compress", config['debug'], config['silent'])

    log.debug("Looking for videos to skip compression")

    dbvideos = database.next_video_to_compress()
    comp = compression.Compression(config)

    for dbvideo in dbvideos:
        if comp.check_exists(dbvideo) is not False:
            database.update_video(dbvideo, 6)
            log.info("Skipping compression for {} from {}" .format(
                dbvideo.filename, dbvideo.vidname))


def compress(config):
    """
        Main function for compressing
        Does everything
        Returns nothing
    """
    log = logger.Logger("Compress", config['debug'], config['silent'])

    comp = compression.Compression(config)

    log.debug("Compressing initialised")
    log.debug("Looking for videos to compress")

    dbvideos = database.next_video_to_compress()

    for dbvideo in dbvideos:
        dbvideo.filename = utils.strip_accents(dbvideo.filename)
        dbvideo.filename = utils.clean_special_chars(dbvideo.filename)

        if comp.check_exists(dbvideo) is not False:

            database.update_video(dbvideo, 5)

            log.info("Compressing {} from {}" .format(
                dbvideo.filename, dbvideo.vidname))

            with stopwatch.StopWatch() as t:
                status = comp.compress(
                    args=config['compress']['com'],
                    nice=int(config['compress']['nice']),
                    dbvideo=dbvideo
                )

            if status:
                log.info("Video was compressed and encoded successfully")

                log.info("It took {} minutes to compress {}".format(
                    t.minutes, dbvideo.filename
                )
                )

                database.insert_history(
                    dbvideo,
                    "Compression Completed successfully"
                )

                database.update_video(dbvideo, 6)

                if 'compress' in config['notification']['notify_on_state']:
                    notify.compress_complete(dbvideo)

                comp.cleanup()

            else:
                database.update_video(dbvideo, 4)

                database.insert_history(dbvideo, "Compression failed", 4)

                notify.compress_fail(dbvideo)

                log.info("Compression did not complete successfully")
        else:
            database.update_video(dbvideo, 2)

            database.insert_history(
                dbvideo, "Input file no longer exists", 4
            )

    else:
        log.info("Queue does not exist or is empty")


def extras(config):
    """
        Main function for filebotting and flagging forced subs
        Does everything
        Returns nothing
    """
    log = logger.Logger("Extras", config['debug'], config['silent'])

    fb = filebot.FileBot(config['debug'], config['silent'])

    dbvideos = database.next_video_to_filebot()

    for dbvideo in dbvideos:
        if config['ForcedSubs']['enable']:
            forced = mediainfo.ForcedSubs(config)
            log.info("Attempting to discover foreign subtitle for {}.".format(dbvideo.vidname))
            track = forced.discover_forcedsubs(dbvideo)

            if track is not None:
                log.info("Found foreign subtitle for {}: track {}".format(dbvideo.vidname, track))
                log.debug("Attempting to flag track for {}: track {}".format(dbvideo.vidname, track))
                flagged = forced.flag_forced(dbvideo, track)
                if flagged:
                    log.info("Flagging success.")
                else:
                    log.debug("Flag failed")
            else:
                log.debug("Did not find foreign subtitle for {}.".format(dbvideo.vidname))
                
        log.info("Attempting video rename")

        database.update_video(dbvideo, 7)

        movePath = dbvideo.path
        if config['move']:
            if dbvideo.vidtype == "tv":
                movePath = config['tvPath']
            else:
                movePath = config['moviePath']

        status = fb.rename(dbvideo, movePath)

        if status[0]:
            log.info("Rename success")

            database.update_video(dbvideo, 6)

            if config['filebot']['subtitles']:
                log.info("Grabbing subtitles")

                status = fb.get_subtitles(
                    dbvideo, config['filebot']['language'])

                if status:
                    log.info("Subtitles downloaded")
                    database.update_video(dbvideo, 8)

                else:
                    log.info("Subtitles not downloaded, no match")
                    database.update_video(dbvideo, 8)

                log.info("Completed work on {}".format(dbvideo.vidname))

                if config['commands'] is not None and len(config['commands']) > 0:
                    for com in config['commands']:
                        subprocess.Popen(
                            [com],
                            stderr=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            shell=True
                        )

            else:
                log.info("Not grabbing subtitles")
                database.update_video(dbvideo, 8)



            if 'extra' in config['notification']['notify_on_state']:
                notify.extra_complete(dbvideo)

            log.debug("Attempting to delete %s" % dbvideo.path)

            try:
                os.rmdir(dbvideo.path)
            except OSError as ex:
                if ex.errno == errno.ENOTEMPTY:
                    log.debug("Directory not empty")

        else:
            log.info("Rename failed")

    else:
        log.info("No videos ready for filebot")


if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version=__version__)
    config = yaml.safe_load(open(CONFIG_FILE))

    config['debug'] = arguments['--debug']

    config['silent'] = arguments['--silent']
    
    if arguments['--force_db'] not in ['tv','movie', None]:
        raise ValueError('{} is not a valid DB.'.format(arguments['--force_db']))
    else:
        config['force_db'] = arguments['--force_db']

    workDir = config['workDir']
    if not os.path.exists(workDir):
        os.makedirs(workDir)

    logger.workDir = workDir
    database.set_path(os.path.join(workDir, "autorippr.sqlite"))
        
    notify = notification.Notification(
        config, config['debug'], config['silent'])

    if bool(config['analytics']['enable']):
        analytics.ping(__version__)

    if arguments['--test']:
        testing.perform_testing(config)

    if arguments['--rip'] or arguments['--all']:
        rip(config)

    if (arguments['--compress'] or arguments['--all']) and not arguments['--skip-compress']:
        compress(config)

    if arguments['--skip-compress']:
        skip_compress(config)

    if arguments['--extra'] or arguments['--all']:
        extras(config)
