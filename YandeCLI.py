#!/usr/bin/python
# -*- coding: utf-8 -*-
from os       import chdir
from json     import loads
from crawler  import Main
from argparse import ArgumentParser
from logging  import basicConfig, DEBUG, INFO, WARNING, ERROR, CRITICAL
def main():
    parser = ArgumentParser(description = 'A crawler for yande.re')
    parser.add_argument('-v', '--version', action = 'version', version = 'Yande.re Crawler v1.8 by cloudwindy')
    parser.add_argument('-p', '--prefix', default = '.', help = 'specify prefix directory')
    parser.add_argument('-c', '--conf', default = 'config.json', help = 'specify config file path')
    args = parser.parse_args()
    chdir(args.prefix)
    file = open(args.conf, 'r')
    conf = loads(file.read())
    file.close()
    basicConfig(level=DEBUG, format='[%(asctime)s %(name)s %(levelname)s] %(message)s', filename=conf['log_file'], filemode='w')
    Main(range(conf['start'], conf['end'], conf['step']), conf['tags'], conf['thread_num'], conf['save_dir']).run()

if __name__ == '__main__':
    main()
