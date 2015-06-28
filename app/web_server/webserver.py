#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('..')
sys.path.append('../../libs')
sys.path.append('../..')

import string
import getopt
from flask import Flask, render_template,request
import mongoengine
from config import Config
import json
import random
import time
import threading
import socket

from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop


## Initializing the app
app = Flask(__name__)
app.debug = True
config = Config()
host_conf = None
monitors = [dict(ip="localhost", port=7006)]
PERIOD_BEAT = 3
## Main pages
@app.route('/')
def index():
    return render_template('index.html')

#Return a fortune : line randomly selected in a file
@app.route('/fortune', methods=['GET', 'POST'])
def fortune():
    if request.method == 'GET':
        file_fortune = open("../"+config.fortune_service.path_file_fortunes, 'r')
        selected_line = random.choice(file_fortune.readlines()) #No close in that call since file closes automatically after call.
        response = dict(host_conf=host_conf, result=selected_line)
        print "line selected : " +selected_line
        i=0
        time.sleep(2)
        #nb = raw_input('Choose a number: ')

        return json.dumps(response)
    elif request.method == 'POST':
        #selected_line = random.choice(open(config.fortune_service.path_file_fortunes, 'r').readlines()) #No close in that call since file closes automatically after call.
        response = dict(ok=False)#, result=selected_line)
        return json.dumps(response)

#def monitorDaemon(server_ip, server_port,load_bal_ip, load_bal_port):
    

def heartbeatDaemon(source_port,monitors_received):
    while True:
        hbSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for monitor in monitors_received:
            hbSocket.sendto("heartbeat#%d"%int(source_port), (monitor['ip'],int(monitor['port'])))
        time.sleep(PERIOD_BEAT)

if __name__ == "__main__":
    (options, args) = getopt.getopt(sys.argv[1:], "s:l:h",
        ["source=", "loadBal=", "help"])
    source_port, load_bal_ip, load_bal_port = None, None, None
    for opt, val in options:
        if (opt in ("-s", "--source")):
            source_port = int(val)
        if (opt in ("-l", "--loadBal")):
            (load_bal_ip, load_bal_port) = val.split(":")
            #send notification to load_balancer
            hbSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            hbSocket.sendto("add_server#%s#%d"%("localhost", source_port), (load_bal_ip, load_bal_port))
    ip = "localhost"

    heartbeat_thread = threading.Thread(name='heartbeat', target=heartbeatDaemon, args=(source_port,monitors)) #Care about lists as arguments, if not in [] then list is split
    heartbeat_thread.setDaemon(True)
    heartbeat_thread.start()

    db = mongoengine.connect("%s#%d"%(ip,source_port))
    #db.dropdatabase("%s#%d"%(ip,source_port))


    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(source_port)
    host_conf = {'ip': ip, 'port':int(source_port)}
    IOLoop.instance().start()
    #app.run(host=ip, port=int(port), debug=True)
   # app.run(host=config.fortune_service.ip, port=int(port), debug=True)