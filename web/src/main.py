import bottle
import bottle_sqlite
from bottle import static_file
from bottle import route, run, template, request
from bottle import jinja2_view as view, jinja2_template as template

#from datetime import datetime
#from collections import deque
#import math
#import re
import json
#import logging
#import base64

app = bottle.app()
plugin = bottle_sqlite.SQLitePlugin('../../database.db')
app.install(plugin)

# handlers

@app.get('/static/<filename:path>')
def static(filename):
    return static_file(filename, './static')

@app.get('/')
def index():
    return template('templates/index.html')


@app.get('/chord')
def chord():
    return template('templates/chord.html')


@app.get('/json/connections')
def json_connections(db):
    query = db.execute("""
                       SELECT
                       users.login, contributors.contributions,
                       repos_with_owner.repo_name, repos_with_owner.repo_owner_login
                       FROM contributors
                       LEFT JOIN users on contributors.user_id = users.id
                       LEFT JOIN repos_with_owner on contributors.repo_id = repos_with_owner.repo_id
                       WHERE contributors.user_id = 998068;
                       """)
    results = query.fetchall()
    json_results = [{'contributor': r[0], 'contributions': r[1], 'repo': r[2], 'owner': r[3]}
                   for r in results]
    return json.dumps(json_results, indent=1)


#@app.get('/uploadhackers')
#def upload_hackers():
#    return template('templates/uploadhackers.html')


#@app.post('/upload')
#def upload(db):
#    inputstring = request.forms.get('hackers')
#    hackers = filter(lambda s: s != '',
#                     re.split('[ ,\t\n]+', inputstring))
#    logging.info('hackers = %s' % str(hackers))
#    out = []
#    for login in hackers:
#        db.execute('INSERT OR IGNORE INTO hacker (login) VALUES (?)', (login,))
#        out.append(login)
#    return str(out)


# run

bottle.run(app=app, server='cherrypy', reloader=True)
