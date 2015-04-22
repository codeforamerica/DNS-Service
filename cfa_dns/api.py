from sys import stderr
from urlparse import urlparse, urljoin
from urllib import urlencode
from hashlib import sha1
import json

from socket import getaddrinfo, AF_INET, SOCK_STREAM
from xml.etree.ElementTree import fromstring as parse_xml

from requests import get

def check_upstream(api_proxy_base, api_key):

    _, hostname, _, _, _, _ = urlparse(api_proxy_base)
    ((_, _, _, _, (ip_addr, _)), ) = getaddrinfo(hostname, 443, AF_INET, SOCK_STREAM)

    query = dict(
        UserName='codeforamerica',
        ApiUser='codeforamerica', 
        ApiKey=api_key,
        SLD='codeforamerica',
        TLD='org',
        Command='namecheap.domains.dns.getHosts',
        ClientIp=ip_addr
        )
    
    got = get(api_proxy_base + '?' + urlencode(query))
    tree = parse_xml(got.content)
    
    for el in tree.iter('{http://api.namecheap.com/xml.response}Error'):
        raise ValueError('Upstream API error: {}'.format(el.text))
    
    hosts, expected_hash = [], None
    
    for el in tree.iter('{http://api.namecheap.com/xml.response}host'):
        host = dict(
            type=el.attrib['Type'],
            name=el.attrib['Name'],
            value=el.attrib['Address'],
            ttl=el.attrib['TTL'],
            mxpref=el.attrib['MXPref']
            )
        
        if (host['type'], host['name']) == ('TXT', 'hosts-hash'):
            expected_hash = host['value']
            continue
        
        hosts.append(tuple(sorted(host.items())))

    serialized = json.dumps(sorted(hosts), ensure_ascii=True, separators=(',', ':'))
    found_hash = sha1(serialized).hexdigest()
    
    if expected_hash != found_hash:
        raise ValueError('Found hash {} but expected {}'.format(found_hash, expected_hash))
    
    print >> stderr, 'Remote host checks out with self-consistent hash'
