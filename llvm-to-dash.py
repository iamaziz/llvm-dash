import requests, sqlite3, os, urllib
from bs4 import BeautifulSoup as bs


# download html documentation
cmdcommand = """ cd . && sh download-llvm.sh """
os.system(cmdcommand)


# CONFIGURATION
docset_name = 'LLVM.docset'
output = docset_name + '/Contents/Resources/Documents/'

# create docset directory
if not os.path.exists(output): os.makedirs(output)

# add icon
icon = 'http://d2wwfe3odivqm9.cloudfront.net/wp-content/uploads/2013/12/llvm-logo-100x100.png'
urllib.urlretrieve(icon, docset_name + "/icon.png")


def update_db(name, typ, path):

	try:
	  cur.execute("SELECT rowid FROM searchIndex WHERE path = ?", (path,))
	  dbpath = cur.fetchone()
	  cur.execute("SELECT rowid FROM searchIndex WHERE name = ?", (name,))
	  dbname = cur.fetchone()

	  if dbpath is None and dbname is None:
	      cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, typ, path))
	      print('DB add >> name: %s, path: %s' % (name, path))
	  else:
	      print("record exists")
	
	except:
		pass


def add_urls():

  # index pages
  pages = {
    'Instruction'	: 'http://llvm.org/docs/ProgrammersManual.html',
    'Category'		: 'http://llvm.org/docs/LangRef.html',
    'Command'		: 'http://llvm.org/docs/CommandGuide/index.html',
    'Guide'			: 'http://llvm.org/docs/GettingStarted.html',
    'Sample'		: 'http://llvm.org/docs/tutorial/index.html',
    'Service'		: 'http://llvm.org/docs/Passes.html'
      }
  
  base_path = './'

  # loop through index pages:
  for p in pages:
    typ = p
    # soup each index page
    html = requests.get(pages[p]).text
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
      	update_db(name, typ, path)


def add_infoplist():
  name = docset_name.split('.')[0]
  info = " <?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
         "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\"> " \
         "<plist version=\"1.0\"> " \
         "<dict> " \
         "    <key>CFBundleIdentifier</key> " \
         "    <string>{0}</string> " \
         "    <key>CFBundleName</key> " \
         "    <string>{1}</string>" \
         "    <key>DocSetPlatformFamily</key>" \
         "    <string>{2}</string>" \
         "    <key>isDashDocset</key>" \
         "    <true/>" \
         "    <key>isJavaScriptEnabled</key>" \
         "    <true/>" \
         "    <key>dashIndexFilePath</key>" \
         "    <string>{3}</string>" \
         "</dict>" \
         "</plist>".format(name, name, name, 'index.html')
  open(docset_name + '/Contents/Info.plist', 'wb').write(info)

# create and open SQLite db
db = sqlite3.connect(docset_name + '/Contents/Resources/docSet.dsidx')
cur = db.cursor()
try:
    cur.execute('DROP TABLE searchIndex;')
except:
    pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

# start
add_urls()
add_infoplist()

# commit and close db
db.commit()
db.close()
