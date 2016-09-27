import os
import json
import requests
import logging
from alerta.app import app
from alerta.plugins import PluginBase
LOG = logging.getLogger('alerta.plugins.influxdb')
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.DEBUG)
INFLUXDB_URL = os.environ.get('INFLUXDB_URL') or app.config.get('INFLUXDB_URL')
INFLUXDB_USER = os.environ.get('INFLUXDB_USER') or app.config.get('INFLUXDB_USER')
INFLUXDB_PASSWORD = os.environ.get('INFLUXDB_PASSWORD') or app.config.get('INFLUXDB_PASSWORD')


class InfluxDBWrite(PluginBase):

    def pre_receive(self, alert):
        return alert

    def post_receive(self, alert):
        url = INFLUXDB_URL + '/write?db=telegraf&rp=default'
        data = "errors_history,environment={},event={},resource={},severity={} value={} ".format(alert.environment,alert.event,alert.resource,alert.severity,alert.value)
        LOG.debug('InfluxDB data: %s', data)
        try:
            response = requests.post(url=url, data=data)
        except Exception as e:
            raise RuntimeError("InfluxDB connection error: %s", e)

        LOG.debug('InfluxDB response: %s', response)

    def status_change(self, alert, status, text):
        return
