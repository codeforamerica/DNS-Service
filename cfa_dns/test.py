from sys import argv
from . import check_file
    
if __name__ == '__main__':
    _, filename = argv
    check_file(filename)
