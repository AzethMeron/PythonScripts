
from pytube import YouTube
from pytube import Playlist
import os
import glob
from time import sleep
from multiprocessing import Process
import configparser
import shutil
import ffmpeg
global PLAYLIST_URLS, VIDEO_URLS, TARGET_RESOLUTION, NUMBER_OF_THREADS, DELAY_MS, MAX_RETRIES
# by Jakub Grzana

# Simple Python script to download videos and playlists from youtube, with usage of multiprocessing
# input is done via global variables below. Note this program DOESN'T check the input, it assumes you put right things in
# In general, there's almost no error management here.
# Comments might be outdated. Currently, files 'playlists.txt', 'videos.txt' and 'download_yt.ini' are used for input



# PLAYLIST_URLS - list of strings, put URLs to playlists inside. 
# You can download whole channel easily this way. Each channel has playlist with all videos inside
PLAYLIST_URLS = []
try:
    playlist_file = open('playlists.txt', 'r')
    PLAYLIST_URLS = [ url for url in playlist_file.readlines() ]
    playlist_file.close()
except:
    pass

# VIDEO_URLS - list of strings, put URLs to particular videos inside. 
# Note downloading singular videos isn't multiprocessed - for large number of videos, it is better to create playlist
VIDEO_URLS = []
try:
    video_file = open('videos.txt','r')
    VIDEO_URLS = [ url for url in video_file.readlines() ]
    video_file.close()
except:
    pass

config = configparser.ConfigParser()
config.read('download_yt.ini')

# TARGET_RESOLUTION - string, containing resolution you aim for
# Resolutions: '144p', '240p', '360p', '480p', '720p', '1080'
# If specified resolution isn't available for specific video, the best available one is chosen
TARGET_RESOLUTION = config['Default']['TARGET_RESOLUTION'] if 'TARGET_RESOLUTION' in config['Default'] else '1080p'

# NUMBER_OF_THREADS - number of videos to be downloaded simultaneously
# One thread usually doesn't make full use of your bandwidth
# Tho downloading too many videos at one time may result in errors (Youtube might consider you a DDoSer, or your will be jammed, with not enough transfer to actually progress any of your downloads)
NUMBER_OF_THREADS = int(config['Default']['NUMBER_OF_THREADS']) if 'NUMBER_OF_THREADS' in config['Default'] else 8

# DELAY_MS - number of miliseconds to wait after downloading any video
# I heard this might be useful to avoid Youtube anti-ddos, but so far i didn't had to use it at all
DELAY_MS = int(config['Default']['DELAY_MS']) if 'DELAY_MS' in config['Default'] else 50

# I'm not sure what this does, i think pytube automatically retries downloading on error, and here's number of such retries
MAX_RETRIES = int(config['Default']['MAX_RETRIES']) if 'MAX_RETRIES' in config['Default'] else 50

# for audio
TARGET_BITRATE = int(config['Default']['TARGET_BITRATE']) if 'TARGET_BITRATE' in config['Default'] else None

# Requirements:
#   Python 3.9.0
#   pytube 10.7.2
#   ffmpeg, don't know the version

verbose_downloads = int(config['Default']['VERBOSE_DOWNLOADS']) if 'VERBOSE_DOWNLOADS' in config['Default'] else 1 # each Xth prompt will be displayed

def split_list(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def EnsureDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# TODO major feature  - support for non-progressive formats
def DownloadVideo(path, video, target_res, retries, tmp_dir, target_bitrate):
    title = video.title.replace('/',' ').replace('|',' ')
    if path:
        if glob.glob(path + "/" + title + ".*"):
            return False
    else:
        if glob.glob(title + ".*"):
            return False
    video_stream = None
    streams = video.streams
    if target_res:
        video_stream = streams.filter(progressive=True).filter(res=target_res).order_by('resolution')
        if not video_stream:
            video_stream = streams.filter(res=target_res).order_by('resolution')
    if not video_stream:
        video_stream = streams.order_by('resolution')
    video_stream = video_stream.desc().first()
    if video_stream.is_progressive:
        video_stream.download(output_path=path, filename=title, max_retries=retries)
    else:
        audio_stream = None
        audio_stream = streams.filter(type='audio').filter(abr=target_bitrate).first()
        if not audio_stream:
            audio_stream = streams.filter(type='audio').order_by('bitrate').desc().first()
        vid_file = video_stream.download(output_path=tmp_dir, filename="vid", max_retries=retries)
        audio_file = audio_stream.download(output_path=tmp_dir, filename="audio", max_retries=retries)
        fpath = ""
        if path:
            fpath = path + "/"
        fpath = fpath + title + ".mp4"
        ffmpeg.output(ffmpeg.input(vid_file), ffmpeg.input(audio_file), fpath).run(quiet=True)
    return False

def ProcessVidList(path, videos, target_res, delay, retries, target_bitrate):
    pid = os.getpid()
    i = 0
    EnsureDir(str(pid))
    for video in videos:
        EnsureDir(str(pid))
        try:
            video.check_availability()
        except Exception as e:
            print("Skipping. Unavailable video: " + video.title + "\nReason: " + str(e))
            continue
        if (i%verbose_downloads) == 0:
            print("Subprocess " + str(pid) + ": downloading " + str(i+1) + "/" + str(len(videos)))
        i = i + 1
        try:
            if DownloadVideo(path, video, target_res, retries, str(pid), target_bitrate):
                continue
        except Exception as e:
            print("Omitting due to error: " + str(e))
            continue
        if delay > 0:
            sleep(delay*0.001)
        shutil.rmtree(str(pid))

def DownloadPlaylist(playlist, target_res):
    dir = playlist.title.replace('/',' ')
    EnsureDir(dir)
    list_of_vidz = list(playlist.videos)
    splitted = list(split_list(list_of_vidz, NUMBER_OF_THREADS))
    threads = []
    for vid_list in splitted:
        thread = Process(target=ProcessVidList, args=(dir, vid_list, target_res, DELAY_MS, MAX_RETRIES, TARGET_BITRATE,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    for video in [ YouTube(url) for url in VIDEO_URLS ]:
        print("Downloading video: " + video.title)
        EnsureDir('temp')
        DownloadVideo(None, video, TARGET_RESOLUTION, MAX_RETRIES, 'temp', TARGET_BITRATE)
        shutil.rmtree('temp')
    for playlist in [ Playlist(url) for url in PLAYLIST_URLS ]:
        print("Downloading playlist: " + playlist.title)
        DownloadPlaylist(playlist, TARGET_RESOLUTION)