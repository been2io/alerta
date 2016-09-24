#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Invoke weixin api to send zabbix alerts.
Author	: Moby <moby.huang@musical.ly>
Date	: 23:50 6-Feb-2016
'''
touser: 成员ID列表（消息接收者，多个接收者用‘|’分隔，最多支持1000个）。特殊情况：指定为@all，则向关注该企业应用的全部成员发送
toparty: 部门ID列表，多个接收者用‘|’分隔，最多支持100个。当touser为@all时忽略本参数
totag: 标签ID列表，多个接收者用‘|’分隔。当touser为@all时忽略本参数
msgtype: 消息类型，此时固定为：text
agentid: 企业应用的id，整型。可在应用的设置页面查看
content: 消息内容
safe: 表示是否是保密消息，0表示否，1表示是，默认0
'''
'''
接口返回值参考:
    {"errcode":0,"errmsg":"ok"}
    {"errcode":40001,"errmsg":"invalid credential"}
    {"errcode":40014,"errmsg":"invalid access_token"}
    {"errcode":41001,"errmsg":"access_token missing"}
    {"errcode":42001,"errmsg":"access_token expired"}
    {"errcode":45009,"errmsg":"api freq out of limit"}
    {"errcode":82001,"errmsg":"All touser & toparty & totag invalid"}
'''
"""
import json
import os
import re
import requests
import sys
from alerta.app import severity_code,app,status_code
from time import time
from alerta.plugins import PluginBase, RejectException
import logging
from os.path import expanduser
from expiringdict import ExpiringDict
from dateutil import tz
#SECRET = {
#    'corpid': 'wxa4e276dc9c2e1f23',
#    'corpsecret': '2BuJ_FjH_CGAgTH694AGQmEr_Y4Ir7TT9nKHVQ-ifoDMDkUHaKNM-3-fW3agDg4v',
#}  # MusicallyMonitor

SECRET = {
    'corpid': 'wx54a9417a974934c3',
    'corpsecret': 'I78G46sZyFc3EyKtTe3GhPThTbztnu8H9vi69jAMRhyOW5BGifEpD-WqheLg4LfN',
}  # 备用 MusicallyMonitor2

# SECRET = {
#     'corpid': 'wxbee5fdf09414010c',
#     'corpsecret': 'KkWq18zEycDLGvxA4aorym8gyiOO25-elMPuUyQzQgOjurq0bkc8GC-RB7Z-7yuq',
# }  # 调试用 MusicallyOps

# app ids
APPS = {'Average': 1, 'High': 4, 'Disaster': 5, 'Lively': 6}

# reverse search rules for users
USERS = {
    'cooper.du': {
        'keywords': [
            'cloud_zuul_direct',
            'cloud_feeds_consumer_follow',
            'Free disk',
            'docker_pilot',
            'musical_delete lag',
            'feeds_user_followed lag',
            'active_delet_outbox_store lag',
            'user_follow_edit_solr'
        ]
    },
    'david.han': {},
    'ivan.fu': {},
    'michael.song': {},
    'muxi.zhang': {},
    'ralph.jiang': {},
    'shawock.zhou': {},
    'terry.ma': {},
    'xiang.chen': {},
    'moby.huang': {},
    'yan.yin': {},
    'jumper.ma': {},
    'arthur.zhu': {
       'keywords': [
            'cloud_',
            'docker_',
            'kafka',
            'cass_',
        ]
     },
    'wen.lin': {
        'keywords': [
            'cloud_zuul',
            'cloud_feeds',
            'Free disk',
            'docker_pool',
            'musical_like',
        ]
    },
    'biao.xue': {
        'keywords': [
            'cloud_zuul',
            'cloud_feeds',
            'Free disk',
            'docker_pool',
            'musical_like',
        ]
    },
    'alex.zhu': {
        'severities': ['Average'],
    },
    'eric.zhou':  {
        'severities': ['Average'],
    },
    'louis.yang':  {
        'severities': ['Average'],
    },
    'francis.yuan': {},

}
LOG = logging.getLogger('alerta.plugins.wechat')
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)
corp_id=app.config.get("WECHAT_ID")
corp_secret=app.config.get("WECHAT_SECRET")
if corp_id and corp_secret:
    LOG.info("set up webchat")
    SECRET['corpid']=corp_id
    SECRET['corpsecret']=corp_secret

class WeChat(PluginBase):
    def __init__(self):
        blackout_time = app.config['WECHAT_BLACKOUT_SECOND']
        LOG.info("wechat blackout second {}".format(blackout_time))
        self.sender= WeixinMsgSender()
        self.alert_history=ExpiringDict(max_len=100000, max_age_seconds=blackout_time)
    def pre_receive(self, alert):
        """Pre-process an alert based on alert properties or reject it by raising RejectException."""
        return alert

    def post_receive(self, alert):
        """Send an alert to another service or notify users."""
        LOG.info('######################################################################')
        LOG.info("id:{}".format(alert.id))
        LOG.info("text:{}".format(alert.text))
        LOG.info("status:{}".format(alert.status))
        if alert.status == status_code.OPEN :
            if not self.alert_history.get(alert.id):
                if alert.severity == severity_code.CRITICAL:
                    text="{}!{}:{}".format(alert.severity,alert.service,alert.resource)
                    if alert.value:
                        text="{} is {}".format(text,alert.value)
                    if alert.last_receive_time:
                        text="{} at {}".format(text,alert.receive_time.replace(tzinfo=tz.tzutc()).astimezone( tz.gettz('Asia/Shanghai')).strftime("%Y/%m/%d %H:%M"))
                    LOG.info("message:{}".format(text))
                    self.sender.send_msg_retry_once("1",'yan.yin',text)
                    self.alert_history[alert.id] = True
                else:
                    LOG.info("ignore none critical alerts")
            else:
                LOG.info("ignore same alerts within {} second,age is {}".format(self.alert_history.max_age,self.alert_history.get(alert.id,default=None,with_age=True)))
        else:
            LOG.info("ignore not open alerts")
        return

    def status_change(self, alert, status, text):
        """Trigger integrations based on status changes."""
        return
def msg_to_receiver(message):
    message = re.sub(r'\n+', '\n', message)

    severity = 'Average'
    for line in message.split('\n'):
        fields = line.split(':')
        if fields[0].strip() == 'Severity':
            severity = fields[1].strip()
            break

    if 'live' in message:
        appid = APPS["Lively"]
    else:
        appid = APPS[severity]

    users = USERS.keys()
    for user, rules in USERS.items():
        if not rules:
            continue
        if rules.get('severities'):
            for s in rules['severities']:
                if s == severity:
                    users.remove(user)
                    break
        if rules.get('keywords'):
            for k in rules['keywords']:
                if k in message:
                    users.remove(user)
                    break
    if users:
        to_user = '|'.join(users)
    else:
        to_user = '@all'

    return appid, to_user


class WeixinMsgSender(object):
    def __init__(self):
        home = expanduser("~")
        self.base_url = 'https://qyapi.weixin.qq.com/cgi-bin/'
        self.token = ''
        self.cache_path = '{}/.zabbix_weixin.cache'.format(home)
        self.cache_age = 7200
        self.load_cache()

    def load_cache(self):
        if os.path.isfile(self.cache_path):
            mod_time = os.path.getmtime(self.cache_path)
            current_time = time()
            if (mod_time + self.cache_age) > current_time:
                try:
                    cache = open(self.cache_path)
                    self.token = cache.read()
                except Exception:
                    pass
            else:
                self.rotate_token(**SECRET)
        else:
            self.rotate_token(**SECRET)

    def rotate_token(self, corpid, corpsecret):
        get_token_url = self.base_url + 'gettoken?corpid={:s}&corpsecret={:s}'.format(corpid, corpsecret)
        print 'Getting token from weixin api'
        resp = requests.get(get_token_url).json()
        print json.dumps(resp, indent=2)
        token = resp['access_token']
        cache = open(self.cache_path, 'w')
        cache.write(token)
        cache.close()
        self.token = token

    def send_msg(self, app_id, to_user, message):
        send_msg_url = self.base_url + 'message/send?access_token={:s}'.format(self.token)
        content = {
            "touser": to_user,
            "agentid": app_id,
            "msgtype": "text",
            "text": {
                "content": message,
            }
        }
        print 'Sending message with token: {}'.format(self.token)
        resp = requests.post(send_msg_url, data=json.dumps(content, ensure_ascii=False)).json()
        print json.dumps(resp, indent=2)
        return int(resp["errcode"])

    def send_msg_retry_once(self,app_id,to_user,message):
        errcode=self.send_msg(app_id,to_user,message)
        if errcode == 0:
            LOG.info("send msg success {}".format(str(message)))
        else:
            if errcode in (41001, 40014, 42001):
                self.rotate_token(**SECRET)
                errcode = self.send_msg(app_id, to_user, message)
                if errcode == 0:
                    LOG.info("send msg success {}".format(str(message)))
                else:
                    LOG.info("send msg failed {}".format(str(message)))
            else:
                print 'Failure, error code: {}'.format(errcode)
                LOG.info("send msg failed {:s}".format(message))
