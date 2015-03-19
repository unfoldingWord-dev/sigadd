#!/usr/bin/env python

import os
import sys
import json
import requests
import ipaddress
import urllib2
import base64
import shlex
from flask import Flask, request, abort
from subprocess import *

app = Flask(__name__)
api_root = '/var/www/vhosts/api.unfoldingword.org/httpdocs'
api_base = 'https://api.unfoldingword.org'
pki_base = 'https://pki.unfoldingword.org'
working_dir = '.sigadd_temp/'


@app.route("/", methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        return json.dumps({'return': 'OK'})

    elif request.method == 'POST':
        # load payload
        try:
            payload = json.loads(request.values.get('data'))
        except Exception as e:
            return json.dumps({'error':e.message})

        # read fields
        if 'slug' not in payload:
            return json.dumps({'error':'missing the "slug"'})
        slug = payload['slug']

        if 'sig' not in payload:
            return json.dumps({'error':'missing the "sig"'})
        sig = payload['sig']

        if 'content' not in payload:
            return json.dumps({'error':'missing the "content"'})
        content = payload['content']

        # validate api base
        if not content.startswith(api_base):
            return json.dumps({'return': 'Error: Wrong content URL.'})
        path = content.split(api_base)[1]
        path = path.split('?')[0]

        check = checkSig(path, sig, slug)
        if not check:
            return json.dumps({'return': 'Error: Sig does not match content.'})

        addSig(path, sig, slug)
        return json.dumps({'return': 'OK'})

def checkSig(path, sig, slug):
    vk_url = '{0}/si/{1}-vk.pem'.format(pki_base, slug)
    if slug == 'uW':
        vk_url = '{0}/{1}-vk.pem'.format(pki_base, slug)
    try:
        f = urllib2.urlopen(vk_url)
        vk_content = f.read()
    except Exception as e:
        return False

    # parse SI
    # si = parseSI(vk_content)
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    keyf = open(working_dir+'pub.pem', 'w')
    keyf.write(vk_content)
    keyf.close()

    sigf = open(working_dir+'content.sig', 'w')
    sigf.write(sig)
    sigf.close()

    # Use openssl to verify that sig works against content at path
    # TODO: this is not working
    command = shlex.split('openssl dgst -sha384 -verify '+keyf.name+' -signature '+sigf.name+' '+path)
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate()

    return True

def parseSI(si_content):
    '''
    Splits a SI (Signing Identity) into it's three components.
    1. Public key
    2. Organization info
    3. Signature
    '''
    lines = si_content.split('\n')
    pk = ''
    org = ''
    sig = ''
    for line in lines:
        line = line.strip()
        if line.startswith('-----'):
            section = line
        elif line:
            if section == '-----BEGIN PUBLIC KEY-----':
                pk += line
            elif section == '-----BEGIN ORG INFO-----':
                org += line
            elif section == '-----BEGIN SIG-----':
                sig += line

    return {'pk':base64.b64decode(pk), 'org':base64.b64decode(org), 'sig':base64.b64decode(sig)}

def addSig(path, sig, slug):
    sig_json = json.loads('[]')
    sig_path = '{0}{1}'.format(api_root, path).replace('json', 'sig')
    if os.path.exists(sig_path):
        old_f = open(sig_path, 'r')
        sig_json = json.loads(old_f.read())
        old_f.close()
    sig_json.append({ 'si': slug, 'sig': sig })
    f = open(sig_path, 'w')
    f.write(json.dumps(sig_json))
    f.close()

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
