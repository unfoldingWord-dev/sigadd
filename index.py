#!/usr/bin/env python

import os
import sys
import json
import requests
import time
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
working_dir = '.sigadd_temp'


@app.route("/", methods=['GET', 'POST'])
def index():

    if request.method == 'GET':
        return json.dumps({'ok':''})

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
            return json.dumps({'error': 'Wrong content URL.'})
        path = content.split(api_base)[1]
        path = path.split('?')[0]

        check = checkSig(path, sig, slug)
        if not check:
            return json.dumps({'error': 'Sig does not match content.'})

        addSig(path, sig, slug)
        return json.dumps({'ok':''})

def checkSig(path, sig, slug):
    '''
    Checks if a signature is valid
    :param path: the path to the content that was signed
    :param sig: the signature that will be validated
    :param slug: the SI slug
    :return:
    '''
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

    ts = time.time()
    keyf = open('{0}/{1}.pem'.format(working_dir, ts), 'w')
    keyf.write(vk_content)
    keyf.close()

    sigf = open('{0}/{1}.sig'.format(working_dir, ts), 'w')
    sigf.write(sig)
    sigf.close()

    # Use openssl to verify that sig works against content at path
    # TODO: this is not working
    content_path = '{0}{1}'.format(api_root, path)
    command_str = 'openssl dgst -sha384 -verify '+keyf.name+' -signature '+sigf.name+' '+content_path
    command = shlex.split(command_str)
    com = Popen(command, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    out, err = com.communicate()

    # cleanup
    os.remove(keyf.name)
    os.remove(sigf.name)

    if err:
        print err

    return True #not err

def parseSI(si_content):
    '''
    @deprecated
    Splits a SI (Signing Identity) into it's three components.
    1. Public key
    2. Organization info
    3. Signature
    :param si_content: the contents of the SI file that was downloaded
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
    '''
    Adds a signature to the list of valid signatures for the content
    :param path: the path to the signatures file
    :param sig: the signature to add
    :param slug: the SI slug
    '''
    sig_json = json.loads('[]')
    sig_path = '{0}{1}'.format(api_root, path).replace('json', 'sig')

    # load existing sigs
    if os.path.exists(sig_path):
        old_f = open(sig_path, 'r')
        sig_json = json.loads(old_f.read())
        old_f.close()

    # remove old sig
    i = 0
    while i < len(sig_json):
        if sig_json[i].get('si') == slug:
            print 'removed '+slug+' from list'
            sig_json.pop(i)
        else:
            # TRICKY: we don't increment when we pop because the list length is shorter by one
            i += 1

    # append new sig
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
