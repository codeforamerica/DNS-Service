from sys import stderr
from urlparse import urlparse, urljoin
from urllib import urlencode
from itertools import count
from hashlib import sha1
import json

from socket import getaddrinfo, AF_INET, SOCK_STREAM
from xml.etree.ElementTree import fromstring as parse_xml

from requests import get, post

api_defaults = dict(
    UserName='codeforamerica',
    ApiUser='codeforamerica', 
    SLD='codeforamerica',
    TLD='org'
    )

def format_csv_row(row):
    ''' Format row from input CSV so it is ready for hash_host_records().
    
        Return a sorted list of two-element tuples.
    '''
    return sorted([('type', row['Type']), ('name', row['Host']),
                   ('value', row['Value']), ('ttl', row['TTL']),
                   ('mxpref', row['MXPref'] or '0')])

def format_xml_element(el):
    ''' Format element from API response so it is ready for hash_host_records().
    
        Return a sorted list of two-element tuples.
    '''
    return sorted([('type', el.attrib['Type']), ('name', el.attrib['Name']),
                   ('value', el.attrib['Address']), ('ttl', el.attrib['TTL']),
                   ('mxpref', el.attrib['MXPref'])])

def hash_host_records(formatted_records):
    '''
    '''
    kwargs = dict(ensure_ascii=True, separators=(',', ':'))
    serialized = json.dumps(sorted(formatted_records), **kwargs)
    return sha1(serialized).hexdigest()

def get_proxy_ipaddr(api_proxy_base):
    ''' Get an IP address based on the API proxy URL.
    
        NameCheap uses IP address white-listing to secure their DNS records
        API, while this app is designed to be hosted on Heroku with its
        unstable IP addresses. So, we use an HTTP proxy to route requests
        from a stable location.
    '''
    _, hostname, _, _, _, _ = urlparse(api_proxy_base)
    ((_, _, _, _, (ip_addr, _)), ) = getaddrinfo(hostname, 443, AF_INET, SOCK_STREAM)
    
    return ip_addr

def check_upstream(api_proxy_base, api_key):
    ''' Check connectivity and consistency of NameCheap-hosted records.
    
        Throw exceptions if a problem is found, otherwise return nothing.
    '''
    query = dict(
        ApiKey=api_key,
        Command='namecheap.domains.dns.getHosts',
        ClientIp=get_proxy_ipaddr(api_proxy_base)
        )
        
    query.update(api_defaults)
    
    got = get(api_proxy_base + '?' + urlencode(query))
    tree = parse_xml(got.content)
    
    for el in tree.iter('{http://api.namecheap.com/xml.response}Error'):
        raise ValueError('Upstream API error: {}'.format(el.text))
    
    hosts, expected_hash = [], None
    
    for el in tree.iter('{http://api.namecheap.com/xml.response}host'):
        if (el.attrib['Type'], el.attrib['Name']) == ('TXT', 'hosts-hash'):
            expected_hash = el.attrib['Address']
        else:
            hosts.append(format_xml_element(el))

    found_hash = hash_host_records(hosts)
    
    if expected_hash != found_hash:
        raise ValueError('Calculated hash {} but expected {}'.format(found_hash, expected_hash))
    
    print >> stderr, 'Remote host checks out with hash "{}"'.format(found_hash)

def push_upstream(api_proxy_base, api_key, host_records):
    ''' Post replacement host records to NameCheap.
    
        Throw exceptions if a problem is found, otherwise return nothing.
    '''
    hash = hash_host_records(map(format_csv_row, host_records))
    
    form = dict(
        ApiKey=api_key,
        Command='namecheap.domains.dns.setHosts',
        ClientIp=get_proxy_ipaddr(api_proxy_base),

        # Hash record is the first record.
        HostName1='hosts-hash',
        RecordType1='TXT',
        Address1=hash,
        MXPref1=0,
        TTL1=300
        )
    
    form.update(api_defaults)
    
    for (record, number) in zip(host_records, count(2)):
        form.update({
            'HostName{:d}'.format(number): record['Host'],
            'RecordType{:d}'.format(number): record['Type'],
            'Address{:d}'.format(number): record['Value'],
            'MXPref{:d}'.format(number): record['MXPref'] or '0',
            'TTL{:d}'.format(number): record['TTL']
            })
    
    posted = post(api_proxy_base, data=form)
    tree = parse_xml(posted.content)
    
    for el in tree.iter('{http://api.namecheap.com/xml.response}Error'):
        raise ValueError('Upstream API error: {}'.format(el.text))
    
    if posted.status_code not in range(200, 299):
        raise Exception('Bad response status {}'.format(posted.status_code))
