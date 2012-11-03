#!/usr/bin/env python
#-=- encoding: utf-8 -=-


from flask import Flask
#from flask import jsonify
from flask import render_template
from email.parser import Parser
from email.header import decode_header
import email
import re
from jinja2 import evalcontextfilter, Markup, escape

import imaplib

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

app = Flask(__name__)

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

@app.template_filter()
def parse_payload(msg):
    msg = re.sub(r'\r(?!=\n)', '\r\n', msg)
    msg  = email.message_from_string(msg)
    payload = msg.get_payload(decode=True)
    print payload
    return header_filter(payload)

@app.template_filter('decode_header')
def header_filter(s, idx=0):
        _s = decode_header(s)
        if len(_s) <= idx:
            header = ""
        else:
            header = _s[idx][0].decode(_s[idx][1] or 'latin-1')
        print header
        print '-----------------'
        return header

@app.route("/login")
def login():
    try:
        login_plain(i, 'username@domain.com', 'password')
        #i.login('username@domain.com', 'password')
        return('Loggued in!')
    except:
        return('ERROR')

def list_boxes():
    return i.list()

@app.route("/mails")
@app.route("/mails/")
@app.route("/mails/<box>")
def list_mails(box='INBOX'):
    return render_template('list_mails.html', box=box, **list_mails_api(box))

def list_mails_api(box='INBOX'):
    state, msg = i.select(box)
    boxes=list_boxes()
    if msg[0] == '0':
        mails = "No messages in {0}".format(box)
    else:
        mails = i.fetch('1:*', '(UID body[header.fields (from to subject date)])')
    mails = [
            (x[0].split(' ')[2].strip(')'),
            Parser().parsestr(x[-1]))
            for x in mails[1]
            if len(x) > 1
            ]
    return {'boxes': boxes, 'mails': mails}

@app.route("/mails/<box>/<mailid>")
def read_mail(box, mailid):
    i.select(box)
    mail = read_mail_api(box, mailid)['msg']
    return render_template('read_mail.html', msg=mail)

def read_mail_api(box, mailid):
    i.select(box)
    mail = i.fetch(mailid, '(BODY.PEEK[HEADER.FIELDS (Date To Cc From Subject X-Priority Content-Type) ] BODY.PEEK[1.2])')
    print mail[1][0][1]
    return {'msg':Parser().parsestr(mail[1][0][1])}

@app.route("/")
def hello():
    return "Hello World!"

def login_plain(imap, user, password, authuser=None):
    def plain_callback(response):
        if authuser is None:
            return "%s\x00%s\x00%s" % (user, user, password)
        else:
            return "%s\x00%s\x00%s" % (user, authuser, password)
    return imap.authenticate('PLAIN', plain_callback)

i = imaplib.IMAP4_SSL(host='mail.domain.tld')
login_plain(i, 'username', 'password')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
