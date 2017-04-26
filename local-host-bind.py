#!/usr/bin/env python
# -*- coding: utf-8 -*-
# version: release

from __future__ import division
from string import Template
import os
import sys
import mmap
import logging


reload(sys)
sys.setdefaultencoding('utf-8')

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

DOCSWEB = os.environ.get('DOCSWEB')

template = '''
## Welcome To Home
$body
'''


def gen_index(urls, port):
    links = []
    for i, url in enumerate(urls[1:]):
        link = 'http://localhost:%d/%s' % (port, url)
        doc_name = url
        links.append('[%s](%s) %s' % (doc_name, link, url))
    links_join = '\n\n' . join(links)
    mdfile = os.path.join(DOCSWEB, 'index', 'docs', 'index.md')
    t = Template(template)
    data = t.substitute(body=links_join)
    with (open(mdfile, 'w')) as f:
        f.write(data)
    cmd = 'cd %s' % os.path.join(DOCSWEB, 'index')
    cmd = cmd + ' && mkdocs build -t amelia -c -d docs-html'
    log.info(cmd)
    os.system(cmd)
    # remove googleapi, because it let the page be loading so slowly.
    filename = os.path.join(DOCSWEB, 'index', 'docs-html', 'css', 'bootstrap-custom.min.css')
    f = open(filename, "r+")
    data = mmap.mmap(f.fileno(), os.path.getsize(filename))
    start = 0
    end = data.find(";") + 1
    length = end - start
    size = len(data)
    newsize = size - length
    data.move(start, end, size - end)
    data.flush()
    data.close()
    f.truncate(newsize)


def web_startup(port):
    cmd = 'cd %s' % DOCSWEB
    cmd = cmd + ' && python -m SimpleHTTPServer %d' % port
    os.system(cmd)


if __name__ == '__main__':
    urls = [
        'index/docs-html',
        'notebook/site',
        'laravel-china.org/docs/5.1',
        'www.golaravel.com/laravel/docs/5.0',
        'lumen.laravel-china.org/docs',
        'flask-docs',
        'flask-docs-html',
        'explore-flask/docs-html',
        'click-docs-html',
        'ahkcn.github.io',
        'tornado-docs',
        'tornado-docs-html',
        'doc.redisfans.com',
        'docker-doc.readthedocs.org/zh_CN/latest',
        'docs.phpcomposer.com',
        'manual.51yip.com/python',
        'notice501.github.com',
        'pyspider-docs-html',
        'pyspider-docs-ch/book',
        'pyquery',
        'python-docs-simple-old/new/docs-html',
        'python-2.7.13-docs-html',
        'python-3.6.1-docs-html',
        'python.usyiyi.cn',
        'scrapy-doc-chs/build/html',
        'scrapy-doc-chs-latest',
        'scrapyd-doc-html/html',
        'selenium-docs-html',
        'selenium-doc/docs-html',
        'www.php2python.com',
        'zsh_html'
    ]
    port = 8888

    if DOCSWEB is None:
        log.error('Please set env "DOCSWEB" first.')
        sys.exit(1)

    gen_index(urls, port)
    log.info('http://localhost:%d/index/docs-html/' % port)
    web_startup(port)