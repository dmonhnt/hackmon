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
	hackdb.execute("insert into wordlist (target_id, keyword) values(%s, %s)", (target_id, keyword))
	print "Number of Rows Updated: ", hackdb.rowcount
	return;	
	
def target_show(hackdb):
	hackdb.execute("select * from targets")
	rows = hackdb.fetchall()
	print "target_id target_name"
	for row in rows:
		print row[0], row[2]
	return;

def monitor(hackdb):
	hackdb.execute("select location from sources where enabled = 1")
	srcs = hackdb.fetchall()
	for src in srcs:
		f = feedparser.parse(src[0])
		for i in range(0,10):
        		date = f.entries[i].published
        		uid = hashlib.md5(f.entries[i].link).hexdigest()
        		link = f.entries[i].link
       	 		data = f.entries[i].content
			print date,uid,link,data
			#check for base keywords
				#if hit, load in DB & check for targets
				#insert hit for each target
	return;

#Parse the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--check', help='Check the database connection', action='store_true', default=False)
parser.add_argument('--tadd', help='Add a new target')
parser.add_argument('--tshow', help='Show current targets', action="store_true", default=False)
parser.add_argument('--fadd', help='Add a new feed')
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
#elif fadd is not None:
#	feed_add(hackdb,fadd)	
elif args.mon:
	monitor(hackdb)

#write changes to DB
dbcon.commit()
