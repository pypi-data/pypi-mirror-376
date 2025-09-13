#!/usr/bin/python

import os
import sys
import unittest
import re

from stormshield.sns.sslclient import SSLClient

APPLIANCE = os.getenv('APPLIANCE', "")
PASSWORD = os.getenv('PASSWORD', "")
SSLVERIFYPEER = os.getenv('SSLVERIFYPEER', "1") == "1";

@unittest.skipIf(APPLIANCE=="", "APPLIANCE env var must be set to the ip/hostname of a running SNS appliance")
@unittest.skipIf(PASSWORD=="", "PASSWORD env var must be set to the firewall password")
class TestFormatIni(unittest.TestCase):
    """ Test INI format """

    def setUp(self):
        self.client = SSLClient(host=APPLIANCE, user='admin', password=PASSWORD, sslverifyhost=False, sslverifypeer=SSLVERIFYPEER)

        self.maxDiff = 5000

    def tearDown(self):
        self.client.disconnect()

    def test_raw(self):
        """ raw format """

        expected_re = """101 code=00a01000 msg="Begin" format="raw"
AUTH.*
CHPWD.*
100 code=00a00100 msg="Ok\""""

        response = self.client.send_command('HELP')

        self.assertTrue(re.match(expected_re, response.output, re.MULTILINE|re.DOTALL))
        self.assertEqual(response.ret, 100)

    def test_section(self):
        """ section format """

        expected = {
            "Global": {
                "State": "0",
                "RiskHalfLife": "21600",
                "RiskTTL": "86400"
            },
            "Alarm": {
                "Minor": "2",
                "Major": "10"
            },
            "Sandboxing" : {
                "Suspicious": "2",
                "Malicious": "50",
                "Failed": "0"
            },
            "Antivirus": {
                "Infected": "100",
                "Unknown": "2",
                "Failed": "0"
            }
        }

        response = self.client.send_command('CONFIG HOSTREP SHOW')

        self.assertEqual(response.data, expected)
        self.assertEqual(response.ret, 100)

    def test_section_line(self):
        """ section_line format """

        expected = {
            'Object': [
                {'type': 'host', 'global': '0', 'name': '_TestHost1', 'ip': '10.10.5.5', 'modify': '1', 'comment': ''},
                {'type': 'host', 'global': '0', 'name': '_TestHost2', 'ip': '10.10.5.6', 'modify': '1', 'comment': ''},
                {'type': 'host', 'global': '0', 'name': '_TestHost3', 'ip': '10.10.5.7', 'modify': '1', 'comment': ''}
            ]
        }

        self.client.send_command('CONFIG OBJECT HOST NEW name=_TestHost1 ip=10.10.5.5')
        self.client.send_command('CONFIG OBJECT HOST NEW name=_TestHost2 ip=10.10.5.6')
        self.client.send_command('CONFIG OBJECT HOST NEW name=_TestHost3 ip=10.10.5.7')

        response = self.client.send_command('CONFIG OBJECT LIST type=host search=_Test* searchfield=name start=0')

        self.client.send_command('CONFIG OBJECT HOST DELETE name=_TestHost1')
        self.client.send_command('CONFIG OBJECT HOST DELETE name=_TestHost2')
        self.client.send_command('CONFIG OBJECT HOST DELETE name=_TestHost3')

        self.assertEqual(response.data, expected)
        self.assertEqual(response.ret, 100)

    def test_list(self):
        """ list format """

        expected = {'Result': ['network_internals', 'labo_networks']}

        response = self.client.send_command('CONFIG WEBADMIN ACCESS SHOW')

        self.assertEqual(response.data, expected)
        self.assertEqual(response.ret, 100)

    def test_xml(self):
        """ xml text output """

        expected = """<?xml version="1.0"?>
<nws code="100" msg="OK"><serverd ret="101" code="00a01000" msg="Begin"><data format="xml"><filters total_lines="5">
<separator nb_elements="2" first_ruleid="1" position="1" color="c0c0c0" comment="Remote Management: Go to System - Configuration to setup the web administration application access" collapse="0" />
<filter position="2" index="1" type="local_filter_slot" action="pass" status="active" comment="Admin from everywhere"><noconnlog disk="0" syslog="0" ipfix="0" /><from><target value="any" type="any" /></from><to><port value="firewall_srv" type="single" /><port value="https" type="single" /><target value="firewall_all" type="group" /></to></filter>
<filter position="3" index="2" type="local_filter_slot" action="pass" status="active" ipproto="icmp" proto="none" icmp_type="8" icmp_code="0" comment="Allow Ping from everywhere"><noconnlog disk="0" syslog="0" ipfix="0" /><from><target value="any" type="any" /></from><to><target value="firewall_all" type="group" /></to></filter>
<separator nb_elements="1" first_ruleid="3" position="4" color="c0c0c0" comment="Default policy" collapse="0" />
<filter position="5" index="3" type="local_filter_slot" action="block" status="active" comment="Block all"><noconnlog disk="0" syslog="0" ipfix="0" /><from><target value="any" type="any" /></from><to><target value="any" type="any" /></to></filter>
</filters>
</data></serverd><serverd ret="100" code="00a00100" msg="Ok"></serverd></nws>"""

        response = self.client.send_command('CONFIG FILTER EXPLICIT index=1 type=filter output=xml')

        self.assertEqual(response.xml, expected)
        self.assertEqual(response.ret, 100)

if __name__ == '__main__':
    unittest.main()
