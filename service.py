#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2014 KODeKarnage
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import xbmc
import xbmcaddon
import json
import xbmcgui


__addon__        = xbmcaddon.Addon('service.nextplaying.song')
__addonid__      = __addon__.getAddonInfo('id')
__setting__      = __addon__.getSetting
script_path       = __addon__.getAddonInfo('path')
addon_path       = xbmc.translatePath('special://home/addons')

play_position_query = {"jsonrpc": "2.0","method": "Player.GetItem","params": {"properties": ['totaltime'],"playerid": 0},"id": "1"}


def grab_settings():
    notification_offset = int(float(__setting__('notice_offset')))
    notification_timing = int(float(__setting__('notice_timing')))
    logging    = True if __setting__('logging') == 'true' else False

    return notification_offset, notification_timing, logging

notification_offset, notification_timing, logging = grab_settings()

def log(msg, label=''):

    if logging:

        if label:
            combined_message = 'service.nextplaying.song ::-:: ' + str(label) + ' = ' + str(msg)
        else:
            combined_message = 'service.nextplaying.song ::-:: ' + str(msg)

        xbmc.log(msg=combined_message)

def runtime_converter(time_string):
    if time_string == '':
        return 0
    else:
        x = time_string.count(':')

        if x ==  0:
            return int(time_string)
        elif x == 2:
            h, m, s = time_string.split(':')
            return int(h) * 3600 + int(m) * 60 + int(s)
        elif x == 1:
            m, s = time_string.split(':')
            return int(m) * 60 + int(s)
        else:
            return 0

def lang(id):
    san = __addon__.getLocalizedString(id).encode( 'utf-8', 'ignore' )
    return san 

class myMonitor(xbmc.Monitor):

    def __init__(self, nextsong_player):
        self.nextsong_player = nextsong_player
        xbmc.Monitor.__init__(self)


    def onSettingsChanged(self):

        global notification_offset
        global notification_timing
        global logging

        notification_offset, notification_timing, logging = grab_settings()
        self.nextsong_player.notification_timing = notification_timing





class myPlayer(xbmc.Player):

    def __init__(self, notification_timing):
        self.notification_timing = notification_timing
        self.whats_playing_query = {"jsonrpc": "2.0","method": "Player.GetItem","params": {"properties": [],"playerid": 0},"id": "1"}
        self.playlist_contents_query = {"jsonrpc": "2.0","method": "Playlist.GetItems","params": {"properties": ["artist","album", "albumid", "thumbnail","duration"],"playlistid": 0},"id": "1"}
        
        self.playback_string = ''
        self.playback_time = ''

        self.onPlayBackStarted()


    def onPlayBackStopped(self):
        self.onPlayBackEnded()


    def onPlayBackEnded(self):
        self.playback_string = ''
        self.playback_time = ''


    def onPlayBackStarted(self):

        myquery = json.dumps(self.whats_playing_query)
        
        result = xbmc.executeJSONRPC(myquery)
        whats_playing = unicode(result, 'utf-8', errors='ignore')
        whats_playing = json.loads(whats_playing)

        log(whats_playing, 'whats playing ')

        if 'result' in whats_playing:

            if 'item' in whats_playing['result']:

                wp = whats_playing['result']['item']

                playing_id = wp.get('id','')

                log(playing_id, 'playing id ')

                if playing_id:
        
                    myquery = json.dumps(self.playlist_contents_query)
                    
                    result = xbmc.executeJSONRPC(myquery)
                    playlist_contents = unicode(result, 'utf-8', errors='ignore')
                    playlist_contents = json.loads(playlist_contents)  

                    log(playlist_contents, 'playlist contents query') 
                    
                    if 'result' in playlist_contents:

                        if 'items' in playlist_contents['result']:

                            pc = playlist_contents['result']['items']

                            log(pc, 'playlist contents')           

                            jank = False

                            sd = {}
                            
                            for song in pc:

                                if 'id' in song:

                                    if jank:
                                        sd = song
                                        break

                                    if song.get('id','') == playing_id:
                                        jank = True

                            if sd:

                                album_name  = sd.get('album','')
                                song_name   = sd.get('label','')
                                album_id    = sd.get('albumid','')
                                song_id     = sd.get('id','')
                                thumbnail   = sd.get('thumbnail','')
                                artist_list = sd.get("artist",'')

                                if artist_list:

                                    try:
                                        artist_list.append('')
                                        artist = artist_list[0]

                                    except:

                                        artist = artist_list

                                    note = artist + ' - ' + album_name + ' - ' + song_name

                                else:

                                    note = album_name + ' - ' + song_name

                                self.playback_string = "Notification(%s,%s,%i,%s)" % (lang(32001),note,self.notification_timing * 1000,thumbnail)



def Main():

    nextsong_player = myPlayer(notification_timing)

    monit = myMonitor(nextsong_player)

    while not xbmc.abortRequested:

        xbmc.sleep(500)

        if nextsong_player.playback_string:

            # log(notification_offset)

            # log(runtime_converter(xbmc.getInfoLabel('MusicPlayer.TimeRemaining')))

            if runtime_converter(xbmc.getInfoLabel('MusicPlayer.TimeRemaining')) <= notification_offset:

                xbmc.executebuiltin(nextsong_player.playback_string)



if __name__ == "__main__":
    Main()
