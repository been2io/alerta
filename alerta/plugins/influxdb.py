import numbers
import os
import json
import requests
import logging
from alerta.app import app
from alerta.plugins import PluginBase
LOG = logging.getLogger('alerta.plugins.influxdb')
LOG.setLevel(logging.DEBUG)
INFLUXDB_URL = os.environ.get('INFLUXDB_URL') or app.config.get('INFLUXDB_URL')
INFLUXDB_USER = os.environ.get('INFLUXDB_USER') or app.config.get('INFLUXDB_USER')
INFLUXDB_PASSWORD = os.environ.get('INFLUXDB_PASSWORD') or app.config.get('INFLUXDB_PASSWORD')


class InfluxDBWrite(PluginBase):
    def __init__(self):
        LOG.info("influxdb")
        LOG.info("host:{}".format(INFLUXDB_URL))
    def pre_receive(self, alert):
        return alert

    def post_receive(self, alert):
        url = INFLUXDB_URL + '/write?db=telegraf&rp=default'
        data = "alerts_history,environment={},event={},resource={},severity={}".format(alert.environment,alert.event,alert.resource,alert.severity).replace(" ","\ ")
        data = "{} alert_id=\"{}\"".format(data,alert.id)
        try:
            float(data)
            data = "{},value={}".format(data,alert.value)
        except Exception as e:
            pass
        LOG.debug('InfluxDB data: %s', data)
        try:
            response = requests.post(url=url, data=data)
        except Exception as e:
            LOG.error("InfluxDB connection error: %s", e)

        LOG.debug('InfluxDB response: %s', response)

    def status_change(self, alert, status, text):
        return
