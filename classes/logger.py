# -*- coding: utf-8 -*-
"""
Simple logging class


Released under the MIT license
Copyright (c) 2012, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""

import logging
import os
import sys

workDir = os.path.dirname(os.path.abspath(__file__))

class Logger(object):

    def __init__(self, name, debug, silent):
        self.silent = silent

        frmt = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            "%Y-%m-%d %H:%M:%S"
        )

        if debug:
            loglevel = logging.DEBUG
        else:
            loglevel = logging.INFO

        self.createhandlers(frmt, name, loglevel)

    def __del__(self):
        if not self.silent:
            self.log.removeHandler(self.sh)
        self.log.removeHandler(self.fh)
        self.log = None

    def createhandlers(self, frmt, name, loglevel):
        self.log = logging.getLogger(name)
        self.log.setLevel(loglevel)

        if not self.silent:
            self.sh = logging.StreamHandler(sys.stdout)
            self.sh.setLevel(loglevel)
            self.sh.setFormatter(frmt)
            self.log.addHandler(self.sh)

        self.fh = logging.FileHandler(os.path.join(workDir, 'autorippr.log'))
        self.fh.setLevel(loglevel)
        self.fh.setFormatter(frmt)
        self.log.addHandler(self.fh)

    def debug(self, msg):
        self.log.debug(msg)

    def info(self, msg):
        self.log.info(msg)

    def warn(self, msg):
        self.log.warn(msg)

    def error(self, msg):
        self.log.error(msg)

    def critical(self, msg):
        self.log.critical(msg)
