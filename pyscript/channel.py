from pyscript import document, window, WebSocket
import asyncio
import json
from time import sleep
import inspect
import sys


def iscoroutinefunction(obj):
    is_micropython = "micropython" in sys.version.lower()
    if is_micropython:
        if "<closure <generator>" in repr(obj):
            return True
        return inspect.isgeneratorfunction(obj)
    return inspect.iscoroutinefunction(obj)


ChannelHTML = '''<h3 id='title{num}'>Channel Setup</h3>
<table>
  <tr>
    <td><button id='channel_connect{num}'>connect</button></td>
    <td><div id='live{num}' style="background-color: red; width: 10px; height: 10px; border-radius: 5px; display: inline-block;"></div></td>
    <td>channel</td>
    <td><input id='topic{num}' maxlength=50 type='text' value={dtopic} style='color:#0000FF'></td>
    <td>=</td>
    <td style="width: 100px; text-align: center"><label id="channelValue{num}">0</label></td>
    <td><input id='payload{num}' maxlength=50 type='text' value='send this'></td>
    <td><button id="send{num}">Send</button></td>
  </tr>
</table>
<div style='color:#0000FF; width: 800px' id="activity{num}"></div>
'''


class CEEO_Channel:
    def __init__(self, channel, user, project, divName='all_things_channels',
                 suffix='_test', default_topic="''"):
        self.filter = None
        self.value = 0
        self.reply = ''
        self.callback = None
        self.color = 'green'
        self.url = ''
        self.socket = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2

        self.channel, self.user, self.project, self.suffix = channel, user, project, suffix
        self.channeldiv = document.getElementById(divName)
        self.channeldiv.innerHTML = ChannelHTML.format(num=suffix, dtopic=default_topic)
        self.topic = document.getElementById('topic' + suffix)
        self.textbox = document.getElementById('channelValue' + suffix)
        self.activity = document.getElementById('activity' + suffix)
        self.liveBtn = document.getElementById('live' + suffix)
        self.to_send = document.getElementById('payload' + suffix)
        self.send_it = document.getElementById('send' + suffix)
        self.send_it.onclick = self.send_btn
        self.c_btn = document.getElementById('channel_connect' + suffix)
        self.c_btn.onclick = self.connect_disconnect

    def connect_disconnect(self, event):
        if self.c_btn.innerText == 'connect':
            self.setupSocket()
            self.c_btn.innerText = 'disconnect'
        else:
            self.c_btn.innerText = 'connect'
            self.close()

    def setupSocket(self):
        self.url = f"wss://{self.user}.pyscriptapps.com/{self.project}/api/channels/{self.channel}"
        window.console.log(self.url)
        self.is_connected = False
        self._web_socket = None
        self.connect()

    async def onmessage(self, event):
        try:
            message = json.loads(event.data)
            await self.on_received(message)
        except:
            window.console.log('on receive error: ', message)

    async def on_received(self, message):
        if message['type'] == 'welcome':
            self.connected = True
            self.activity.innerText = json.dumps(message)
            self.liveBtn.style.backgroundColor = 'green'
        if message['type'] == 'data':
            if message['payload']:
                try:
                    topic, value = self.check(self.topic.value, message)
                    self.reply = json.loads(message['payload'])
                    self.value = self.reply['value']
                    if value:
                        payload = message['payload']
                        msg = payload if len(payload) < 100 else payload[:20] + '...'
                        self.activity.innerText = msg
                        self.textbox.innerText = self.value
                    if self.callback:
                        if iscoroutinefunction(self.callback):
                            await self.callback(message)
                        else:
                            self.callback(message)
                except Exception as e:
                    window.console.log('load error ', message)

    async def send(self, value):
        await self.post('', value)

    async def post(self, filter, value, blink=0.001):
        if not self.is_connected:
            window.console.log('not connected')
            self.activity.innerText = 'Not connected - please connect to the channel first'
            return
        payload = {'topic': filter, 'value': value}
        try:
            self.socket.send(json.dumps(payload))
        except Exception as e:
            window.console.log('post error ', e)
        self.color = 'lightgreen' if self.color == 'green' else 'green'
        self.liveBtn.style.backgroundColor = self.color

    def connect(self):
        def onopen(event):
            self.activity.innerText = f"WebSocket connected: {now()}"
            self.is_connected = True
            self.reconnect_attempts = 0

        def onclose(event):
            self.liveBtn.style.backgroundColor = 'red'
            self.activity.innerText = f"WebSocket disconnected: {now()}"
            self.is_connected = False
            self.reconnect()

        self.socket = WebSocket(url=self.url, onopen=onopen, onclose=onclose,
                                onmessage=self.onmessage)

    def reconnect(self):
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            self.activity.innerText = (
                f"Attempting to reconnect "
                f"({self.reconnect_attempts}/{self.max_reconnect_attempts})"
            )
            sleep(self.reconnect_delay)
            self.connect()

    def check(self, desired_topic, message):
        if message['type'] == 'data' and 'payload' in message:
            p = json.loads(message['payload'])
            topic, value = p['topic'], p['value']
            if desired_topic == "" or topic.startswith(desired_topic):
                return topic, value
        return None, None

    async def send_btn(self, event):
        if not self.is_connected:
            return
        try:
            await self.post(self.topic.value, self.to_send.value)
        except Exception as e:
            print(e)

    def close(self):
        self.socket.close()
        self.reconnect_attempts = self.max_reconnect_attempts
        self.is_connected = False
        self.liveBtn.style.backgroundColor = 'red'
        self.activity.innerText = f"WebSocket disconnected: {now()}"


def now():
    import time
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )
