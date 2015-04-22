from os.path import dirname, join
import unittest

from . import check_file

class TestFile (unittest.TestCase):

    def test_file(self):
        filename = join(dirname(__file__), '..', 'host-records.csv')
        check_file(filename)

if __name__ == '__main__':
    unittest.main()
