#!/usr/bin/env python
import sqlite3, os, urllib, subprocess, hashlib
from bs4 import BeautifulSoup as bs
from shutil import rmtree

# CONFIGURATION
llvm_version = '3.7.0'
llvm_tarball_md5sum = 'b98b9495e5655a672d6cb83e1a180f8e'
tarball_name = 'llvm-%s.src.tar.xz' % llvm_version
docset_name = 'LLVM.docset'
output = docset_name + '/Contents/Resources/Documents/'

def md5(fname):
    hash = hashlib.md5()
    with open(fname) as f:
        for chunk in iter(lambda: f.read(4096), ''):
            hash.update(chunk)
    return hash.hexdigest()

def check_llvm_tarball():
  return md5(tarball_name) == llvm_tarball_md5sum

def download_llvm_tarball():
  if os.access(tarball_name, os.R_OK):
      if check_llvm_tarball():
          print 'using existing tarball'
          return
      print 'removing unusable tarball'
      os.remove(tarball_name)

  tarball_url='http://llvm.org/releases/%s/%s' % (llvm_version, tarball_name)
  print 'downloading %s from %s' % (tarball_name, tarball_url)
  urllib.urlretrieve(tarball_url, tarball_name)

  if not check_llvm_tarball():
      raise IOError('llvm src md5sum check failed')

def extract_llvm_tarball():
  src_name = 'llvm-%s.src' % llvm_version
  tarball_name = src_name + '.tar.xz'
  if os.path.exists(src_name):
    rmtree(src_name)
  subprocess.check_call(['tar', '-xf', tarball_name,  src_name + '/docs',
      src_name + '/examples']);
  cwd = os.getcwd();
  os.chdir(src_name + '/docs');
  subprocess.check_call(['make', '-f', 'Makefile.sphinx', 'BUILDDIR=../../build'])
  os.chdir(cwd)
  os.makedirs(os.path.dirname(output))
  os.rename('build/html', output)

def remove_old_data():
  if os.path.exists(docset_name):
    rmtree(docset_name)

def update_db(db, cur, name, typ, path):
  try:
    cur.execute('SELECT rowid FROM searchIndex WHERE path = ?', (path,))
    dbpath = cur.fetchone()
    cur.execute('SELECT rowid FROM searchIndex WHERE name = ?', (name,))
    dbname = cur.fetchone()

    if dbpath is None and dbname is None:
      cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, typ, path))
      print('DB add >> name: %s, path: %s' % (name, path))
    else:
      print('record exists')

  except:
    pass

def add_urls(db, cur):
  # index pages
  pages = {
          'Instruction'	: 'ProgrammersManual.html',
          'Category'	: 'LangRef.html',
          'Command'	: 'CommandGuide/index.html',
          'Guide'	: 'GettingStarted.html',
          'Sample'	: 'tutorial/index.html',
          'Service'	: 'Passes.html'
          }

  base_path = './'

  # loop through index pages:
  for p in pages:
    typ = p
    # soup each index page
    html = open(output + '/' + pages[p], 'r').read()
    soup = bs(html)
    for a in soup.findAll('a'):
      name = a.text.strip()
      path = a.get('href')

      name = name.replace('\n', '')
      filtered = ('index.html', 'http')

      if path is not None and len(name) > 2 and not path.startswith(filtered):
        dirpath = ['Command', 'Sample']
        if p in dirpath:
            path = pages[p].split('/')[-2] + '/' + path
        if path.startswith('#'):
            path = base_path + pages[p].split('/')[-1] + path
        else:
            path = base_path + path

        # Populate the SQLite Index
        update_db(db, cur, name, typ, path)

def add_infoplist():
  name = docset_name.split('.')[0]
  info = ' <?xml version=\'1.0\' encoding=\'UTF-8\'?>' \
          '<!DOCTYPE plist PUBLIC \'-//Apple//DTD PLIST 1.0//EN\' \'http://www.apple.com/DTDs/PropertyList-1.0.dtd\'> ' \
          '<plist version=\'1.0\'> ' \
          '<dict> ' \
          '    <key>CFBundleIdentifier</key> ' \
          '    <string>{0}</string> ' \
          '    <key>CFBundleName</key> ' \
          '    <string>{1}</string>' \
          '    <key>DocSetPlatformFamily</key>' \
          '    <string>{2}</string>' \
          '    <key>isDashDocset</key>' \
          '    <true/>' \
          '    <key>isJavaScriptEnabled</key>' \
          '    <true/>' \
          '    <key>dashIndexFilePath</key>' \
          '    <string>{3}</string>' \
          '    <key>DashDocSetFallbackURL</key>' \
          '    <string>{4}</string>' \
          '</dict>' \
          '</plist>'.format(name, name, name, 'index.html', 'http://llvm.org/releases/3.7.0/docs/')
  open(docset_name + '/Contents/Info.plist', 'wb').write(info)

if __name__ == '__main__':
  remove_old_data()

  # download html documentation
  download_llvm_tarball()
  extract_llvm_tarball()

  # add icon
  icon = 'http://d2wwfe3odivqm9.cloudfront.net/wp-content/uploads/2013/12/llvm-logo-100x100.png'
  urllib.urlretrieve(icon, docset_name + '/icon.png')

  # create and open SQLite db
  db = sqlite3.connect(docset_name + '/Contents/Resources/docSet.dsidx')
  cur = db.cursor()
  cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
  cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

  # start
  add_urls(db, cur)
  add_infoplist()

  # commit and close db
  db.commit()
  db.close()
