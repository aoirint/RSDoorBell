import os
import sys
import json
from wsgiref.simple_server import make_server
import hmac
import hashlib
import base64
import subprocess
import time
from bs4 import BeautifulSoup

from concurrent.futures import ThreadPoolExecutor
import random


HOST = os.environ.get('HOST', 'localhost')
PORT = int(os.environ.get('PORT', 8000))

BELL_MESSAGE = os.environ.get('BELL_MESSAGE')

SECRET_SPEECH = os.environ.get('SECRET_SPEECH')
SECRET_SPEECH_DEV = os.environ.get('SECRET_SPEECH_DEV')
SECRET_BELL = os.environ.get('SECRET_BELL')
SECRET_BELL_DEV = os.environ.get('SECRET_BELL_DEV')


def play(file):
    p = subprocess.Popen([ 'mpg123', file ])
    p.communicate()

def play_msg(msg):
    if msg is None or len(msg) == 0:
        return

    p = subprocess.Popen('open_jtalk -x /var/lib/mecab/dic/open-jtalk/naist-jdic -m mei/mei_normal.htsvoice -r 1.0 -ow /dev/stdout', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)

    text = msg
    text = '  '.join(text.split('\n'))
    if len(text) > 200:
        text = text[:200]

    out, _ = p.communicate(text.encode('utf-8'))
    wav = out

    # TODO: volume up
    p = subprocess.Popen('aplay -', stdin=subprocess.PIPE, shell=True)
    p.communicate(wav)

    #p = subprocess.Popen('ffmpeg -i pipe:0 -f mp3 -af volume=10dB pipe:1', stdin=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    #out, _ = p.communicate(wav)

    #sound = out

    #p = subprocess.Popen('mpg123 -', stdin=subprocess.PIPE, shell=True)
    #p.communicate(sound)

def responseSpeech(env, start_response, rb):
    print('Authorized access to speech')# from %s' % (env['REMOTE_IP'], ))

    data = rb.decode('utf-8')
    data = json.loads(data)

    status = '200 OK'
    headers = [
        ( 'Content-Type', 'application/json' ),
    ]

    response = {
            'type': 'message',
            'text': 'Accepted',
    }

    start_response(status, headers)


    def exec_play():
        play('bell/Chime-Announce03-1.mp3')

        user = data['from']['name']
        text = data['text']

        bs = BeautifulSoup(text, 'html5lib')
        text = bs.text

        #with open('a.json', 'w') as fp:
        #    json.dump(data, fp, ensure_ascii=False)
        msg = '%s からメッセージです。 %s' % ( user, text, )
        print(msg)
        play_msg(msg)

        play('bell/Chime-Announce03-2.mp3')

    tpe.submit(exec_play)

    body = json.dumps(response).encode('utf-8')

    return [ body, ]

def responseBell(env, start_response, rb):
    print('Authorized access to bell')# from %s' % (env['REMOTE_IP'], ))

    data = rb.decode('utf-8')
    data = json.loads(data)

    status = '200 OK'
    headers = [
        ( 'Content-Type', 'application/json' ),
    ]

    response = {
            'type': 'message',
            'text': 'Accepted',
    }

    start_response(status, headers)


    def exec_play():
        play('bell/Chime-Announce03-1.mp3')

        user = data['from']['name']
        text = data['text']
        id = data['from']['aadObjectId']

        bs = BeautifulSoup(text, 'html5lib')
        text = bs.text

        custom_bell_dir = 'custom_bell'
        if os.path.exists(custom_bell_dir):
            bells = os.listdir(custom_bell_dir)
            if len(bells) > 0:
                bell = random.choice(bells)
                bell_path = os.path.join(custom_bell_dir, bell)
                play(bell)

        if BELL_MESSAGE is not None:
            play_msg(BELL_MESSAGE)

        play('bell/Chime-Announce03-2.mp3')

        # you need to see a.json to check the actual user name.. it's not just the display name!!.
        # with open('a.json', 'w') as fp:
        #     json.dump(data, fp, ensure_ascii=False)

    tpe.submit(exec_play)

    body = json.dumps(response).encode('utf-8')

    return [ body, ]

if __name__ == '__main__':
    host = 'localhost'
    #host = '0.0.0.0'
    port = 8990

    tpe = ThreadPoolExecutor(max_workers=1)

    def view(env, start_response):
        info = env['PATH_INFO'][1:]
        method = env['REQUEST_METHOD']
        inp = env['wsgi.input']
        inp_len = int(env['CONTENT_LENGTH'])
        rb = inp.read(inp_len)
        # 発信元検証
        auth = env['HTTP_AUTHORIZATION']
        def match(secret):
            if secret is None:
                return False
            localHMAC = 'HMAC ' + base64.b64encode(hmac.new(base64.b64decode(secret.encode('ascii')), rb, hashlib.sha256).digest()).decode('ascii')
            return auth == localHMAC

        if match(SECRET_SPEECH) or match(SECRET_SPEECH_DEV):
            return responseSpeech(env, start_response, rb)
        elif match(SECRET_BELL) or match(SECRET_BELL_DEV):
            return responseBell(env, start_response, rb)
        else:
            print('Unauthorized access')# from %s' % (env['REMOTE_IP'], ))
            status = '403 Forbidden'
            headers = [
                ('Content-Type', 'application/json'),
            ]

            response = {
            }
            body = json.dumps(response).encode('utf-8')

            start_response(status, headers)
            return [ body, ]


    server = make_server(host, port, view)
    print('Server starts')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    print('Server stopped')
