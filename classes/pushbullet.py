# -*- coding: utf-8 -*-
"""
Pushbullet Class


Released under the MIT license
Copyright (c) 2014, Jason Millward

@category   misc
@version    $Id: 1.7.0, 2016-08-22 14:53:29 ACST $;
@author     Jason Millward
@license    http://opensource.org/licenses/MIT
"""
import logger
import requests

class Pushbullet(object):

    def __init__(self, config, debug, silent):
        self.log = logger.Logger("Pushbullet", debug, silent)
        self.config = config
        
    def send_notification(self, notification_message):
    	r = requests.post("https://api.pushbullet.com/v2/pushes", 
    		data={'type': 'note', 'title': 'AutoRippr', 'body': notification_message},
    		auth=(self.config["api_key"], ''))

    	if r.status_code == 200:
    		self.log.info("Pushbullet message sent successfully")
      	else:
      		self.log.error("Pushbullet message not sent")
