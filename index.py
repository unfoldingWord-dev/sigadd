#!/usr/bin/env python

import os
import sys
import json
import requests
import ipaddress
from flask import Flask, request, abort
from subprocess import *

app = Flask(__name__)
api_root = '/var/www/vhosts/api.unfoldingword.org/httpdocs'
api_base = 'https://api.unfoldingword.org'
pki_base = 'https://pki.unfoldingword.org/'


@app.route("/", methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        return 'OK'

    elif request.method == 'POST':
        payload = json.loads(request.data)
        slug = payload['slug']
        sig = payload['sig']
        content = payload['content']
        if not content.startswith(api_base):
            return json.dumps({'return': 'Error: Wrong content URL.'})
        path = content.split(api_base)[1]

        check = checkSig(path, sig, slug)
        if not check:
            return json.dumps({'return': 'Error: Sig does not match content.'})

        addSig(path, sig, slug)
        return json.dumps({'return': 'OK'})

def checkSig(path, sig, slug):
    vk_url = '{0}/si/{1}-vk.pem'.format(pki_base, si)
    if si == 'uW':
        vk_url = '{0}/{1}-vk.pem'.format(pki_base, si)
    vk_content = getURL(vk_url)
    # Split out actual vk
    # Use openssl to verify that sig works against content at path
    return True

def addSig(path, sig, slug):
    sigj = json.loads({})
    sigf = '{0}/{1}'.format(api_root, path).replace('json', 'sig')
    if os.path.exists(sig)
        sigj = json.loads(codecs.open(sigf, 'r', encoding='utf-8').read())
    sigj.append({ 'si': slug, 'sig': sig })
    writeJSON(path, sigj)



def runCom():
    pass

if __name__ == "__main__":
    try:
        port_number = int(sys.argv[1])
    except:
        port_number = 80
    is_dev = os.environ.get('ENV', None) == 'dev'
    if os.environ.get('USE_PROXYFIX', None) == 'true':
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0', port=port_number, debug=is_dev)
