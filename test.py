#!/usr/bin/python
# -*- coding: utf-8  -*-
'''
test
'''
import sys
sys.path.append("/home/multichill/pywikipedia")
import wikipedia

def main():
    wikipedia.output(u'Testing 1 2 3')

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
