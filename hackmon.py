#!/usr/bin/python

import MySQLdb as mdb
import sys
import argparse
import subprocess
import feedparser
import hashlib

DBHOST = 'localhost'
DBUSER = 'root'
DBPASS = 'malware'
DBNAME = 'hackdb'

def db_connect():

        try:
                con = mdb.connect(DBHOST,DBUSER,DBPASS,DBNAME)

        except mdb.Error, e:
                if con:
                        con.rollback()
                print "Error %d: %s" % (e.args[0], e.args[1])
		sys.exit(1)
	return con;	

def db_check(cur):
	
	try: 

		cur.execute("SELECT VERSION()")
		result = cur.fetchone()
		print "MySQL version: "+str(result[0])

		cur.execute("select count(*) from targets")
		result = cur.fetchone()
		print "Targets Loaded: "+str(result[0])

	except mdb.Error, e:

		print "Error %d: %s" % (e.args[0], e.args[1])
		sys.exit(1)
	return;

def target_add(hackdb, target):
	hackdb.execute("insert into targets (target_name) values (%s)",[target])
	print "Number of Rows Updated: ", hackdb.rowcount
	return;

def keyword_add(hackdb, target_id, keyword):
	hackdb.execute("insert into keywords (target_id, keyword) values(%s, %s)", (target_id, keyword))
	print "Number of Rows Updated: ", hackdb.rowcount
	return;	

def feed_add(hackdb, feed):
	hackdb.execute("insert into sources (location, enabled) values(%s, %s)", (feed,1))
	print "Number of Rows Updated: ", hackdb.rowcount
	return;
	
def target_show(hackdb):
	hackdb.execute("select * from targets")
	rows = hackdb.fetchall()
	print "target_id target_name"
	for row in rows:
		print row[0], row[2]
	return;

def keyword_show(hackdb, target_id):
	hackdb.execute("select keyword from keywords where target_id = %s", [target_id])
	rows = hackdb.fetchall()
	print "keyword"
	for row in rows:
		print row[0]
	return;

def feed_show(hackdb):
	hackdb.execute("select location from sources")
	rows = hackdb.fetchall()
	for row in rows:
		print row[0]
	return;

def monitor(hackdb):
	#get all enabled sources
	hackdb.execute("select location from sources where enabled = 1")
	srcs = hackdb.fetchall()

	#pull down each feed (10 entries each) and parse
	for src in srcs:
		f = feedparser.parse(src[0])
		
		#parse through entries
		for i in range(0,10):
        		date = f.entries[i].published
        		uid = hashlib.md5(f.entries[i].link).hexdigest()
        		link = f.entries[i].link
       	 		data = f.entries[i].content[0].value
			print "Checking: " + link
			
			#see whether entry matches base criteria
			if is_hit(hackdb, -1, data):
				print "--> Feed meets base criteria"
				#save matching entry
				save_file(hackdb, date, uid, link, data)

				#check individual targets
				hackdb.execute("select target_id from targets")
				rows = hackdb.fetchall()
				for row in rows:
					#identify target hits
					if is_hit(hackdb,row[0],data):
						hackdb.execute("select target_name from targets where target_id=%s",[row[0]])
						hits = hackdb.fetchone()
						hit = hits[0]
						print "Hit!!: "+hit[0]			
	return;

def is_hit(hackdb, target_id, content):
        hackdb.execute("select keyword from keywords where target_id = %s", [target_id])
        rows = hackdb.fetchall()
	hit = False
        for row in rows:
                if row[0] in content:
			print "--> Keyword "+row[0]+" matches!"
                        hit = True
        return hit;

def save_file(hackdb, date, uid, link, data):
	##insert the file
	print "Saving File: "+link+ "UID: "+uid
	return;

#Parse the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--check', help='Check the database connection', action='store_true', default=False)
parser.add_argument('--tadd', help='Add a new target')
parser.add_argument('--tshow', help='Show current targets', action="store_true", default=False)
parser.add_argument('--fadd', help='Add a new feed')
parser.add_argument('--fshow', help='Show current feeds', action="store_true", default=False)
parser.add_argument("--kadd", help="Add a keyword for a given target", nargs=2)
parser.add_argument("--kshow", help="Show keywords for a given target")
parser.add_argument('--mon', help='Start monitoring', action='store_true', default=False)
args = parser.parse_args()

#Execute functions based on arguments
dbcon = db_connect()
hackdb = dbcon.cursor()
if args.check:
	db_check(hackdb)
elif args.tadd is not None:
	print args.tadd
	target_add(hackdb,args.tadd)
elif args.tshow:
	target_show(hackdb)
elif args.fadd is not None:
	feed_add(hackdb,args.fadd)
elif args.fshow:
	feed_show(hackdb)
elif args.kadd is not None:
	keyword_add(hackdb,args.kadd[0], args.kadd[1])
elif args.kshow is not None:
	keyword_show(hackdb,args.kshow)	
elif args.mon:
	monitor(hackdb)

#write changes to DB
dbcon.commit()
