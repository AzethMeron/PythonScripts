
from pytube import YouTube
from pytube import Playlist
import os
import glob
from time import sleep
import ffmpeg
from multiprocessing import Process
from multiprocessing import Queue
import configparser
import shutil
import re
global PLAYLIST_URLS, VIDEO_URLS, TARGET_RESOLUTION, NUMBER_OF_THREADS, DELAY_MS, MAX_RETRIES, CONVERT_TO_AUDIO
from datetime import datetime
# by Jakub Grzana

# Simple Python script to download videos and playlists from youtube, with usage of multiprocessing
# input is done via global variables below. Note this program DOESN'T check the input, it assumes you put right things in
# In general, there's almost no error management here.
# Comments might be outdated. Currently, files 'playlists.txt', 'videos.txt' and 'download_yt.ini' are used for input

# There's weakpoint, program searches for best available streams for given extensions in order. So if it finds any usable stream for webm, then it won't bother with mp4
# EVEN IF there's MP4 stream with better quality



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

# should work right now
CONVERT_TO_AUDIO = int(config['Default']['CONVERT_TO_AUDIO']) if 'CONVERT_TO_AUDIO' in config['Default'] else 0

# Requirements:
#   Python 3.9.0
#   pytube - up-to-date one
#   ffmpeg, don't know the version

verbose_downloads = int(config['Default']['VERBOSE_DOWNLOADS']) if 'VERBOSE_DOWNLOADS' in config['Default'] else 1 # each Xth prompt will be displayed

def split_list(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))


def EnsureDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def RemoveDir(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def get_video_stream(streams, target_res, in_subtype):
    s = streams.filter(subtype=in_subtype)
    if target_res:
        if s.filter(res = target_res):
            return s.filter(res = target_res).first()
    return s.order_by('resolution').desc().first()
    
def get_audio_stream(streams, target_bitrate, in_subtype):
    s = streams.filter(subtype=in_subtype)
    if target_bitrate:
        if s.filter(abr = target_bitrate):
            return s.filter(abr = target_bitrate).first()
    return s.get_audio_only(in_subtype)

def merge_streams(output_path, video_stream_filename, audio_stream_filename):
    video = ffmpeg.input(video_stream_filename).video
    audio = ffmpeg.input(audio_stream_filename).audio
    ffmpeg.output(
        video,
        audio,
        output_path,
        vcodec='copy',
        acodec='copy',
    ).run(quiet=True)

def convert_to_audio(output_path, audio_stream_filename):
    ffmpeg.input(audio_stream_filename).output(output_path, acodec="copy").run(quiet=True)


def DownloadVideo(path, video, target_res, retries, tmp_dir, target_bitrate):
    streams = video.streams
    
    # Managing title - it can't have any special characters, only letters - and checking if this video (with any extension) is already downloaded
    title = re.sub(r'\W+', ' ', video.title)
    if path:
        if glob.glob(path + "/" + title + ".*"):
            return False
    else:
        if glob.glob(title + ".*"):
            return False
    
    # If you want to convert those videos into mp3
    if CONVERT_TO_AUDIO:
        audio_stream = get_audio_stream(streams.filter(type='audio'), target_bitrate, 'mp4')
        fpath = ""
        if path:
            fpath = path + "/"
        fpath = fpath + title + ".aac"
        convert_to_audio(fpath, audio_stream.download(output_path=tmp_dir, filename="audio", max_retries=retries))
        return False
    
    # Typical case 
    for extension in [ 'webm', 'mp4' ]:    
        video_stream = get_video_stream(streams.filter(type='video'), target_res, extension)
        
        if not video_stream:
            continue
        
        if video_stream.is_progressive:
            video_stream.download(output_path=path, filename=title+"."+extension, max_retries=retries)
        else:
            audio_stream = get_audio_stream(streams.filter(type='audio'), target_bitrate, extension)
            vid_file = video_stream.download(output_path=tmp_dir, filename="vid", max_retries=retries)
            audio_file = audio_stream.download(output_path=tmp_dir, filename="audio", max_retries=retries)
            fpath = ""
            if path:
                fpath = path + "/"
            fpath = fpath + title + "." + extension
            merge_streams(fpath, vid_file, audio_file)
        return False
        
    # Shouldn't be possible, but we prob want to display error if that happens for any reason
    raise RuntimeError("Couldn't find proper streams for none of supported extensions.")

def ProcessVidList(path, videos, target_res, delay, retries, target_bitrate, queue):
    pid = os.getpid()
    i = 0
    for video in videos:
        try:
            video.check_availability()
        except Exception as e:
            print("Skipping. Unavailable video: " + video.title + "\nReason: " + str(e))
            sleep(delay*0.001 + 0.005)
            continue
        if (i%verbose_downloads) == 0:
            print("Subprocess " + str(pid) + ": downloading " + video.title + " " + str(i+1) + "/" + str(len(videos)))
        i = i + 1
        for j in range(1,retries+1):
            try:
                EnsureDir(str(pid))
                DownloadVideo(path, video, target_res, retries, str(pid), target_bitrate)
                break
            except Exception as e:
                err_mess = "Omitting due to error: " + str(e) + ", video name: " + str(video.title)
                if j == retries:
                    print(err_mess)
                    queue.put(err_mess)
                sleep(delay*0.001 + 0.005)
            
        RemoveDir(str(pid))
        sleep(delay*0.001 + 0.005)
    queue.put(0)

def DownloadPlaylist(title, videos, target_res):
    dir = title.replace('/',' ')
    EnsureDir(dir)
    list_of_vidz = list(videos)
    splitted = list(split_list(list_of_vidz, NUMBER_OF_THREADS))
    threads = []
    failures = []
    for vid_list in splitted:
        queue = Queue()
        thread = Process(target=ProcessVidList, args=(dir, vid_list, target_res, DELAY_MS, MAX_RETRIES, TARGET_BITRATE, queue,))
        thread.start()
        threads.append((thread, queue))
    for (thread, queue) in threads:
        while True:
            val = queue.get()
            if type(val) == int:
                thread.join()
                break
            failures.append(val)
    f = open("failures.txt", "a")
    now = datetime.now().strftime("%d/%m/%Y")
    for error in failures:
        f.write(now + " " + error + "\n")
    f.close()
    return failures

if __name__ == '__main__':

    total_failures = []

    if len(VIDEO_URLS) > 0:
        vidlist = ( YouTube(url) for url in VIDEO_URLS )
        print("Downloading singular videos to videos/ directory")
        total_failures.append(DownloadPlaylist('videos', vidlist, TARGET_RESOLUTION))
        
    for playlist in ( Playlist(url) for url in PLAYLIST_URLS ):
        print("Downloading playlist: " + playlist.title)
        total_failures.append(DownloadPlaylist(playlist.title, playlist.videos, TARGET_RESOLUTION))
    
    print("DOWNLOADING COMPLETE")
    print("Ommited:")
    for failures in total_failures:
        for failure in failures:
            print(failure)
    
    