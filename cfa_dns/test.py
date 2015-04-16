from sys import argv
from csv import DictReader
from urlparse import urlparse
from io import StringIO
from hashlib import sha1
from . import URL_REDIRECT

allowed_types = 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'SOA', URL_REDIRECT
allowed_ttls = range(300, 172801)

needed_csv = u'''Note	Type	Host	Value	TTL
Do not touch.	NS		ns-1640.awsdns-13.co.uk.	172800
Do not touch.	NS		ns-835.awsdns-40.net.	172800
Do not touch.	NS		ns-461.awsdns-57.com.	172800
Do not touch.	NS		ns-1271.awsdns-30.org.	172800
Do not touch.	SOA		ns-1640.awsdns-13.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400	900
'''

def normalize(row):
    return tuple(sorted(row.items()))

def test_file(filename):
    '''
    '''
    needed_rows = list(DictReader(StringIO(needed_csv), dialect='excel-tab'))
    needed_tuples = map(normalize, needed_rows)
    
    with open(filename) as file:
        found_rows = list(DictReader(file))
        found_tuples = map(normalize, found_rows)
    
    # Are all required rows present?
    for needed_tuple in needed_tuples:
        assert needed_tuple in found_tuples
    
    # Are only required NS or SOA records present?
    for found_row in found_rows:
        if found_row['Type'] in ('NS', 'SOA'):
            assert normalize(found_row) in needed_tuples
    
    # Seriously don't mess with the required rows.
    digest = sha1(needed_csv).hexdigest()
    assert digest.startswith('46ff1e53bb3514c6'), 'needed_csv value has been tampered with'
    
    # Are types and TTLs all as expected?
    for (index, row) in enumerate(found_rows):
        row.update(dict(source='{} row {}'.format(filename, index+1)))
    
        assert row['Type'] in allowed_types, '"{Type}" is a bad record type, {source}'.format(**row)
        assert int(row['TTL']) in allowed_ttls, '"{TTL}" is a bad TTL, {source}'.format(**row)
        
        if row['Type'] == URL_REDIRECT:
            scheme = urlparse(row['Value']).scheme
            assert scheme in ('http', 'https'), '"{Value}" is a bad redirect, {source}'.format(**row)
    
if __name__ == '__main__':
    _, filename = argv
    test_file(filename)
