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
from bodystructure import parse_bodystructure

import imaplib
from ConfigParser import ConfigParser

config = ConfigParser()
config.read('config/dev-config.ini')

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


@app.route("/login")
def login():
    try:
        login_plain(i, config.get('imap', 'username'), config.get('imap', 'password'))
        #i.login('username@domain.com', 'password')
        return('Loggued in!')
    except:
        return('ERROR')

def list_boxes():
    return i.list()

def getheader(header_text, default="ascii"):
    """Decode the specified header"""
    headers = decode_header(header_text)
    header_sections = [unicode(text, charset or default)
        for text, charset in headers]
    return u"".join(header_sections)

def getheader_from_dict(header_dict, default="ascii"):
    """Decode the specified header dictionnary"""
    d = {}
    for k in header_dict.keys():
        d[k] = getheader(header_dict[k])
    return d

@app.route("/mails")
@app.route("/mails/")
@app.route("/mails/<box>")
def list_mails(box='INBOX'):
    return render_template('list_mails.html', box=box, **list_mails_api(box))

def list_mails_api(box='INBOX'):
    state, msg = i.select(box)
    boxes=list_boxes()
    if msg[0] == '0':
        mails = None
    else:
        typ, data = i.search(None, 'ALL')
        mails = []
        for num in data[0].split():
            msg_header = fetch_header(num)
            # fetch returns something like
            # [status, [('query', 'message'),')'] ]
            parsed_header = email.message_from_string(msg_header)
            # decode header
            clean_parsed_header = getheader_from_dict(parsed_header)
            mails.append({'id': num, 'msg':clean_parsed_header})
    return {'boxes': boxes, 'mails': mails}

def fetch_header(id):
    return i.fetch(
        id,
        '(UID body[header.fields (from to subject date)])'
    )[1][0][1]

@app.route("/mails/<box>/<mailid>")
def read_mail(box, mailid):
    i.select(box)
    mail = read_mail_api(box, mailid)
    print mail
    return render_template('read_mail.html', **mail)

def get_charset(message, default='ascii'):
    if message.get_content_charset():
        return message.get_content_charset()
    if message.get_charset():
        return message.get_charset()
    return default

# from https://github.com/bpeterso2000/IMAP-Tools/blob/master/bodystructure.py

def get_email_body(mailid, partnum):
    parts = i.fetch(mailid, '(body[{0}.mime] body[{0}])'.format(partnum))[1]
    part = parts[0][1] + parts[1][1]
    _m = email.message_from_string(part)
    return unicode(
        _m.get_payload(decode=True),
        _m.get_charset() or _m.get_content_charset() or 'ascii',
        'replace')


def read_mail_api(box, mailid):
    print i.select(box)
    #mail = i.fetch(mailid, '(BODY.PEEK[HEADER])')
    body_structure = i.fetch(mailid, 'BODYSTRUCTURE')
    print body_structure
    header = fetch_header(mailid)
    parsed_header = email.message_from_string(header)
    # decode header
    clean_parsed_header = getheader_from_dict(parsed_header)
    print clean_parsed_header
    html_body = ""
    text_body = ""
    parsed_bodystructure = parse_bodystructure(body_structure[1][0])
    # if mail is only one part, there is no section number
    if len(parsed_bodystructure) == 1:
        p = parsed_bodystructure[0].split()
        if p[0] == '"text"':
            if p[1] == '"plain"':
                _m = i.fetch(mailid, '(body[])')[1][0][1]
                _m = email.message_from_string(_m)
                print _m
                text_body = unicode(
                        _m.get_payload(),
                        _m.get_charset() or _m.get_content_charset() or 'ascii',
                        'replace')
            elif p[1] == '"html"':
                _m = i.fetch(mailid, '(body[])')[1][0][1]
                _m = email.message_from_string(_m)
                html_body = unicode(
                        _m.get_payload(),
                        _m.get_charset() or _m.get_content_charset() or 'ascii',
                        'replace')
    else:
        for p in parsed_bodystructure:
            p = p.split()
            if len(p) > 1:
                if p[1] == '"text"':
                    if p[2] == '"plain"':
                        text_body += get_email_body(mailid, p[0])
                    elif p[2] == '"html"':
                        html_body += get_email_body(mailid, p[0])
    #print html_body
    #print text_body
    return {'headers': clean_parsed_header,
            'plaintext': text_body,
            'html': html_body,
            'attachements': None}

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

i = imaplib.IMAP4_SSL(host=config.get('imap', 'server'))
login_plain(i, config.get('imap', 'username'), config.get('imap', 'password'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
