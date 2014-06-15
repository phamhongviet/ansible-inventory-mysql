#!/usr/bin/env python2
# Manage Ansible inventory

import MySQLdb
import sys
try:
	import json
except ImportError:
	import simplejson as json

server = 'localhost'
server_port = 3306
db_name = 'ansible_inv'
username = 'ans'
password = '123123'
		
		
# create a JSON list of host to work with Ansible
def grouplist(conn):
	inventory ={}
	cur = conn.cursor()
	cur.execute("SELECT `group`, `type`, `name` FROM groups ORDER BY `group`, `type`, `name`")
	for row in cur.fetchall():
		group = row[0]
		if group is None:
			group = 'ungrouped'
		
		# Add group with empty host list to inventory{} if necessary
		if not group in inventory:
			inventory[group] = {
				'hosts' : [],
				'children' : [],
				'vars' : {}
			}
		if row[1] == 'h':
			inventory[group]['hosts'].append(row[2])
		elif row[1] == 'c':
			inventory[group]['children'].append(row[2])
	cur.execute("SELECT `name`, `key`, `value` FROM vars WHERE `type`=%s ORDER BY `name`", ('g',))
	for row in cur.fetchall():
		group = row[0]
		if group is None:
			group = 'ungrouped'
		
		# Add group with empty host list to inventory{} if necessary
		if not group in inventory:
			inventory[group] = {
				'hosts' : [],
				'children' : [],
				'vars' : {}
			}
		inventory[group]['vars'][row[1]] = row[2]
	cur.close()
	print json.dumps(inventory, indent=4)

	
# add a host or child to DB, safely ignore if host or child exists
def add(conn, group, name, type):
	cur = conn.cursor()
	cur.execute("SELECT COUNT(*) FROM groups WHERE `group`=%s AND `name`=%s AND `type`=%s", (group, name, type))
	row = cur.fetchone()
	if row[0] == 0:
		cur.execute("INSERT INTO groups(`group`, `name`, `type`) values (%s, %s, %s)", (group, name, type))
	cur.close()

	
# delete host(s) or child(ren) from DB
def delete(conn, group, name, type):
	cur = conn.cursor()
	cur.execute("DELETE FROM groups WHERE `group`=%s AND `name`=%s AND `type`=%s", (group, name, type))
	cur.close()

	
# add host/group vars to DB, safely ignore if exists
def addvar(conn, name, type, key, value):
	cur = conn.cursor()
	cur.execute("SELECT COUNT(*) FROM vars WHERE `name`=%s AND `type`=%s AND `key`=%s", (name, type, key))
	row = cur.fetchone()
	if row[0] == 0:
		cur.execute("INSERT INTO vars(`name`, `type`, `key`, `value`) values (%s, %s, %s, %s)", (name, type, key, value))
	else:
		cur.execute("UPDATE vars SET `value`=%s WHERE `name`=%s AND `type`=%s AND `key`=%s", (value, name, type, key))
	cur.close()
	

# delete host/group vars from DB
def delvar(conn, name, type, key):
	cur = conn.cursor()
	if key is None:
		cur.execute("DELETE FROM vars WHERE `name`=%s AND `type`=%s", (name, type))
	else:
		cur.execute("DELETE FROM vars WHERE `name`=%s AND `type`=%s AND `key`=%s", (name, type, key))
	cur.close()
	
	
# return host info
def hostinfo(conn, name):
	cur = conn.cursor()
	cur.execute("SELECT `key`, `value` FROM vars WHERE `name`=%s AND `type`=%s", (name, 'h'))
	infos = {}
	for row in cur.fetchall():
		infos[row[0]] = row[1]
	cur.close()
	print json.dumps(infos, indent=4)

# print help
def printhelp():
	print "Usage: " + sys.argv[0] + " --list"
	print "Usage: " + sys.argv[0] + " --host [host]"
	print "Usage: " + sys.argv[0] + " --addhost [group] [host]"
	print "Usage: " + sys.argv[0] + " --addhostvar [host] [key] [value]"
	print "Usage: " + sys.argv[0] + " --addgroupvar [group] [key] [value]"
	print "Usage: " + sys.argv[0] + " --addchild [group] [child]"
	print "Usage: " + sys.argv[0] + " --delhost [group] [host]"
	print "Usage: " + sys.argv[0] + " --delgroupvar [group] [key]"
	print "Usage: " + sys.argv[0] + " --delhostvar [host] [key]"
	print "Usage: " + sys.argv[0] + " --delchild [group] [child]"
	
	
# main execution	
if __name__ == '__main__':
	con = MySQLdb.connect(host=server, port=server_port, user=username, passwd=password, db=db_name)
	if len(sys.argv) > 1:
		if sys.argv[1] == "--addhost":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --addhost [group] [host]"
			else:
				add(con, sys.argv[2], sys.argv[3], 'h')
		elif sys.argv[1] == "--addchild":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --addchild [group] [child]"
			else:
				add(con, sys.argv[2], sys.argv[3], 'c')
		elif sys.argv[1] == "--addhostvar":
			if len(sys.argv) != 5:
				print "Usage: " + sys.argv[0] + " --addhostvar [host] [key] [value]"
			else:
				addvar(con, sys.argv[2], 'h', sys.argv[3], sys.argv[4])
		elif sys.argv[1] == "--addgroupvar":
			if len(sys.argv) != 5:
				print "Usage: " + sys.argv[0] + " --addgroupvar [group] [key] [value]"
			else:
				addvar(con, sys.argv[2], 'g', sys.argv[3], sys.argv[4])
		elif sys.argv[1] == "--delhost":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --delhost [group] [host]"
			else:
				delvar(con, sys.argv[3], 'h', None)
				delete(con, sys.argv[2], sys.argv[3], 'h')
		elif sys.argv[1] == "--delchild":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --delchild [group] [child]"
			else:
				delete(con, sys.argv[2], sys.argv[3], 'c')
		elif sys.argv[1] == "--delhostvar":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --delhostvar [host] [key]"
			else:
				delvar(con, sys.argv[2], 'h', sys.argv[3])
		elif sys.argv[1] == "--delgroupvar":
			if len(sys.argv) != 4:
				print "Usage: " + sys.argv[0] + " --delgroupvar [group] [key]"
			else:
				delvar(con, sys.argv[2], 'g', sys.argv[3])
		elif sys.argv[1] == "--list":
			if len(sys.argv) != 2:
				print "Usage: " + sys.argv[0] + " --host [host]"
			else:
				grouplist(con)
		elif sys.argv[1] == "--host":
			if len(sys.argv) != 3:
				print "Usage: " + sys.argv[0] + " --host [host]"
			else:
				hostinfo(con, sys.argv[2])
		else:
			printhelp()
	else:
		printhelp()
	con.close()
