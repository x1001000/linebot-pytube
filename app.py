import os, sys, re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, AudioSendMessage, VideoSendMessage
from pytube import YouTube
#from moviepy.editor import *

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# authenticate
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# callback HTTP POST call from LINE
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    for split in event.message.text.split():
        match = re.search('.*youtu.*', split)
        if match:
            url = match.group(0)
            try:
                yt = YouTube(url)
            except Exception as e:
                print('EXCEPTION:', e)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='You下ube被YouTube已讀。。。\n請換個網址再讓我試試。。。'))
                break
            streams = yt.streams
            video_id = yt.video_id
            print(yt.title)

            # DOWNLOAD mp4
            try:
                if streams.get_highest_resolution():
                    print(streams.get_highest_resolution().download(output_path='static',filename=video_id))
                elif streams.first():
                    print(streams.first().download(output_path='static',filename=video_id))
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text='抱歉我找不到載點。。。'))
                    break
            except Exception as e:
                print('EXCEPTION:', e)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='抱歉我似乎壞掉了。。。'))
                break
            
            # DOWNLOAD or EXTRACT m4a
            #video = VideoFileClip('static/YTDL.mp4')
            #audio = video.audio
            #audio.write_audiofile('static/LINE.mp3')
            #video.close()
            #audio.close()
            #text='https://youtube-dl-linebot.herokuapp.com/static/LINE.mp3'
            if streams.get_audio_only():
                print(streams.get_audio_only().download(output_path='static',filename=video_id+'_m4a'))
                os.system(f'mv static/{video_id}_m4a.mp4 static/{video_id}.m4a')
            else:
                os.system(f'ffmpeg -i static/{video_id}.mp4 -vn -c:a copy static/{video_id}.m4a')
            
            # LINE mp4 and m4a
            try:
                line_bot_api.reply_message(
                    event.reply_token,[
                    TextSendMessage(text='敬請手刀下載⬇⬇'),
                    VideoSendMessage(
                        original_content_url=f'https://linebot-pytube.herokuapp.com/static/{video_id}.mp4',
                        preview_image_url=yt.thumbnail_url),
                    AudioSendMessage(
                        original_content_url=f'https://linebot-pytube.herokuapp.com/static/{video_id}.m4a',
                        duration=yt.length * 1000)])
            except Exception as e:
                print('EXCEPTION:', e)
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text='奇怪再試一次。。。'))
            finally:
                break
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='說好的YouTube呢。。。'))


if __name__ == "__main__":
    app.run(host='0.0.0.0')