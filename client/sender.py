import re
import time
import requests
import subprocess
import tornado.ioloop
from client.config import *
from requests.exceptions import ConnectionError
from tornado.web import RequestHandler, Application


class Sender(RequestHandler):
    def __init__(self, application, request, **kwargs):
        self.current_ip = self.get_ip()
        super().__init__(application, request, **kwargs)

    def get_ip(self, ifname=ADSL_IFNAME):
        (status, output) = subprocess.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
            if result:
                new_ip = result.group(1)
                if self.current_ip and self.current_ip != new_ip:
                    self.current_ip = new_ip
                    return new_ip

    def adsl(self):
        status = 0
        dialed = False
        for i in range(3):
            if not dialed:
                print('ADSL Start, Please wait')
                (status, output) = subprocess.getstatusoutput(ADSL_BASH)
                if status == 0:
                    print('ADSL Successfully')
                    dialed = True
                    ip = self.get_ip()
                else:
                    print('ADSL Failed, Please Check')
                    status = '-3'
            if dialed:
                if ip:
                    print('New IP', ip)
                    try:
                        requests.post(SERVER_URL, data={'token': TOKEN, 'port': PROXY_PORT, 'name': CLIENT_NAME})
                        print('Successfully Sent to Server', SERVER_URL)
                        status = '1'
                        break
                    except ConnectionError:
                        print('Failed to Connect Server', SERVER_URL)
                        status = '-1'
                else:
                    print('Get IP Failed')
                    status = '-2'
            time.sleep(1)
        return status

    def get(self, api):
        if api == 'adsl':
            token = self.get_query_argument('token', '')
            command = self.get_query_argument('command', '')
            if token == TOKEN:
                if command == 'reconnect':
                    self.write(self.adsl())


def run():
    application = Application([
        (r'/(.*)', Sender),
    ])
    print('Listening on', SENDER_PORT)
    application.listen(SENDER_PORT, address=SENDER_INTERFACE)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    run()
