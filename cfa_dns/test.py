from sys import argv
from csv import DictReader
from io import StringIO

allowed_types = 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'SOA'
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
    
    # Are types and TTLs all as expected?
    for found_row in found_rows:
        assert found_row['Type'] in allowed_types
        assert int(found_row['TTL']) in allowed_ttls, '"{TTL}" is a bad TTL'.format(**found_row)
    
if __name__ == '__main__':
    _, filename = argv
    test_file(filename)
