from os.path import dirname, join
from urlparse import urlparse, parse_qsl
from csv import DictReader
from io import StringIO
import unittest

from httmock import response, HTTMock

from . import check_file
from .api import hash_host_records, format_csv_row, check_upstream, push_upstream

class TestFile (unittest.TestCase):

    def test_file(self):
        filename = join(dirname(__file__), '..', 'host-records.csv')
        check_file(filename)

class TestAPI (unittest.TestCase):

    STEP_BAD_HASH = 1
    STEP_AFTER_ADD = 2

    HASH_BEFORE = '20bea02f8bf1fe5f9565e24b37353162ef5c73e9'
    HASH_AFTER = '744a86c74b52f6bc4edf2376cb9926630b91dd6b'
    
    api_error_xml = '''<?xml version="1.0" encoding="utf-8"?>
        <ApiResponse Status="ERROR" xmlns="http://api.namecheap.com/xml.response">
          <Errors>
            <Error Number="999">{}</Error>
          </Errors>
          <Warnings />
          <RequestedCommand />
          <Server>PHX01APIEXT01</Server>
          <GMTTimeDifference>--4:00</GMTTimeDifference>
          <ExecutionTime>0</ExecutionTime>
        </ApiResponse>
        '''
    
    hosts_csv_data = u'''Type,Host,Value,TTL,MXPref,Note
A,*.s,23.21.64.76,300,,
CNAME,www,ec2-54-234-33-69.compute-1.amazonaws.com.,60,,The website
MX,@,ASPMX.L.GOOGLE.COM.,300,10,GMail
A,@,54.234.33.69,60,,The website
A,boston,66.220.0.85,1800,,
URL301,network,http://peernetwork.in,1800,,
'''

    api_base, api_key = 'http://example.com/root', '0xWHATWHAT'
    _, api_host, api_path, _, _, _ = urlparse(api_base)

    def response_content(self, step=None):
      '''
      '''
      case = self
      
      def mock_handler(url, request):
        scheme, host, path, _, query, _ = urlparse(url.geturl())
        headers = {'Content-Type': 'text/xml; charset=utf-8'}
        
        if (host, path) == (case.api_host, case.api_path):
            args = dict(parse_qsl(query))
            form = dict(parse_qsl(request.body or ''))
            
            if (request.method, args.get('Command', None)) == ('GET', 'namecheap.domains.dns.getHosts'):
                if args['ApiKey'] != case.api_key:
                    raise ValueError('Bad API key: {}'.format(args['ApiKey']))
            
                body = '''<?xml version="1.0" encoding="utf-8"?>
                    <ApiResponse Status="OK" xmlns="http://api.namecheap.com/xml.response">
                      <Errors />
                      <Warnings />
                      <RequestedCommand>namecheap.domains.dns.getHosts</RequestedCommand>
                      <CommandResponse Type="namecheap.domains.dns.getHosts">
                        <DomainDNSGetHostsResult Domain="codeforamerica.org" EmailType="MX" IsUsingOurDNS="true">
                          <host HostId="69617219" Name="*.s" Type="A" Address="23.21.64.76" MXPref="0" TTL="300" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69617220" Name="@" Type="A" Address="54.234.33.69" MXPref="0" TTL="60" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69617246" Name="boston" Type="A" Address="66.220.0.85" MXPref="0" TTL="1800" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69617319" Name="www" Type="CNAME" Address="ec2-54-234-33-69.compute-1.amazonaws.com." MXPref="0" TTL="60" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69617223" Name="@" Type="MX" Address="ASPMX.L.GOOGLE.COM." MXPref="10" TTL="300" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69739050" Name="hosts-hash" Type="TXT" Address="{hosts_hash}" MXPref="0" TTL="300" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          <host HostId="69617283" Name="network" Type="URL301" Address="http://peernetwork.in" MXPref="0" TTL="1800" AssociatedAppTitle="" FriendlyName="" IsActive="" />
                          {additional_host}
                        </DomainDNSGetHostsResult>
                      </CommandResponse>
                      <Server>PHX01APIEXT01</Server>
                      <GMTTimeDifference>--4:00</GMTTimeDifference>
                      <ExecutionTime>0.013</ExecutionTime>
                    </ApiResponse>
                    '''
            
                vars = dict(additional_host='', hosts_hash=case.HASH_BEFORE)
                
                if step == case.STEP_BAD_HASH:
                    vars['hosts_hash'] = 'xyzygy'
                elif step == case.STEP_AFTER_ADD:
                    vars['additional_host'] = '<host HostId="99999" Name="new" Type="CNAME" Address="example.com." MXPref="0" TTL="60" AssociatedAppTitle="" FriendlyName="" IsActive="" />'
                    vars['hosts_hash'] = case.HASH_AFTER

                return response(200, body.format(**vars), headers=headers)
            
            if (request.method, form.get('Command', None)) == ('POST', 'namecheap.domains.dns.setHosts'):
                if form['ApiKey'] != case.api_key:
                    raise ValueError('Bad API key: {}'.format(form['ApiKey']))
            
                self.assertEqual(form['RecordType8'], 'CNAME')
                self.assertEqual(form['HostName8'], 'new')
                self.assertEqual(form['Address8'], 'example.com.')
                
                return response(200, 'ok')
            
            raise NotImplementedError(request.method, url.geturl())
        
        raise NotImplementedError(url.geturl())
    
      return mock_handler
    
    def test_check_upstream(self):
        '''
        '''
        with HTTMock(self.response_content()):
            check_upstream(self.api_base, self.api_key)
    
        with self.assertRaises(ValueError):
            with HTTMock(self.response_content()):
                check_upstream(self.api_base, '0xFAKESTUFF')
    
        with self.assertRaises(ValueError):
            with HTTMock(self.response_content(self.STEP_BAD_HASH)):
                check_upstream(self.api_base, self.api_key)
    
    def test_hash_consistency(self):
        '''
        '''
        host_records = list(DictReader(StringIO(self.hosts_csv_data)))
        hash = hash_host_records(map(format_csv_row, host_records))
        
        self.assertEqual(hash, self.HASH_BEFORE)
    
    def test_check_changes(self):
        '''
        '''
        host_records = list(DictReader(StringIO(self.hosts_csv_data)))
        host_records.append({'Type': 'CNAME', 'Host': 'new', 'Value': 'example.com.', 'MXPref': '', 'TTL': '60'})
        
        hash = hash_host_records(map(format_csv_row, host_records))
        self.assertEqual(hash, self.HASH_AFTER)

        with HTTMock(self.response_content()):
            push_upstream(self.api_base, self.api_key, host_records)
        
        with HTTMock(self.response_content(self.STEP_AFTER_ADD)):
            check_upstream(self.api_base, self.api_key)

if __name__ == '__main__':
    unittest.main()
