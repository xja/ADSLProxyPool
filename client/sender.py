import re
import subprocess
import tornado.ioloop
from tornado.web import RequestHandler, Application
import time
from client.config import *
import requests
from requests.exceptions import ConnectionError


class Sender(RequestHandler):
    def get_ip(self, ifname=ADSL_IFNAME):
        (status, output) = subprocess.getstatusoutput('ifconfig')
        if status == 0:
            pattern = re.compile(ifname + '.*?inet.*?(\d+\.\d+\.\d+\.\d+).*?netmask', re.S)
            result = re.search(pattern, output)
            if result:
                ip = result.group(1)
                return ip

    def adsl(self):
        sleep_delays = [5, 15, 30, 60]
        status = 0
        for delay in sleep_delays:
            print('ADSL Start, Please wait')
            (status, output) = subprocess.getstatusoutput(ADSL_BASH)
            if status == 0:
                print('ADSL Successfully')
                ip = self.get_ip()
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
            else:
                print('ADSL Failed, Please Check')
                status = '-3'
            time.sleep(delay)
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
