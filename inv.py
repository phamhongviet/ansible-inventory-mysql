#!/usr/bin/env python2
# Manage Ansible inventory

import sys
import MySQLdb
try:
    import json
except ImportError:
    import simplejson as json

server = 'localhost'
server_port = 3306
db_name = 'ansible_inv'
username = 'ans'
password = '123123'


def group_list(conn):
    """Create a JSON list of hosts to work with Ansible"""
    inventory = {}
    cur = conn.cursor()
    cur.execute(
        "SELECT `group`, `type`, `name` FROM groups ORDER BY `group`, `type`, `name`")
    for row in cur.fetchall():
        group = row[0]
        if group is None:
            group = 'ungrouped'

        # Add group with empty host list to inventory{} if necessary
        if group not in inventory:
            inventory[group] = {
                'hosts': [],
                'children': [],
                'vars': {}
            }
        if row[1] == 'h':
            inventory[group]['hosts'].append(row[2])
        elif row[1] == 'c':
            inventory[group]['children'].append(row[2])
    cur.execute(
        "SELECT `name`, `key`, `value` FROM vars WHERE `type`=%s ORDER BY `name`",
        ('g',
         ))
    for row in cur.fetchall():
        group = row[0]
        if group is None:
            group = 'ungrouped'

        # Add group with empty host list to inventory{} if necessary
        if group not in inventory:
            inventory[group] = {
                'hosts': [],
                'children': [],
                'vars': {}
            }
        inventory[group]['vars'][row[1]] = row[2]
    cur.close()
    print json.dumps(inventory, indent=4)


def add(conn, group, name, type):
    """Add a host or child to inventory, safely ignore if host or child exists"""
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM groups WHERE `group`=%s AND `name`=%s AND `type`=%s",
        (group,
         name,
         type))
    row = cur.fetchone()
    if row[0] == 0:
        cur.execute(
            "INSERT INTO groups(`group`, `name`, `type`) values (%s, %s, %s)",
            (group,
             name,
             type))
        conn.commit()
    cur.close()


def delete(conn, group, name, type):
    """Delete host(s) or child(ren) from inventory"""
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM groups WHERE `group`=%s AND `name`=%s AND `type`=%s",
        (group,
         name,
         type))
    conn.commit()
    cur.close()


def addvar(conn, name, type, key, value):
    """Add host/group vars to inventory, safely ignore if exists"""
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM vars WHERE `name`=%s AND `type`=%s AND `key`=%s",
        (name,
         type,
         key))
    row = cur.fetchone()
    if row[0] == 0:
        cur.execute(
            "INSERT INTO vars(`name`, `type`, `key`, `value`) values (%s, %s, %s, %s)",
            (name,
             type,
             key,
             value))
        conn.commit()
    else:
        cur.execute(
            "UPDATE vars SET `value`=%s WHERE `name`=%s AND `type`=%s AND `key`=%s",
            (value,
             name,
             type,
             key))
        conn.commit()
    cur.close()


def delvar(conn, name, type, key):
    """Delete host or group vars from inventory"""
    cur = conn.cursor()
    if key is None:
        cur.execute(
            "DELETE FROM vars WHERE `name`=%s AND `type`=%s", (name, type))
        conn.commit()
    else:
        cur.execute(
            "DELETE FROM vars WHERE `name`=%s AND `type`=%s AND `key`=%s",
            (name,
             type,
             key))
        conn.commit()
    cur.close()


def hostinfo(conn, name):
    """Return host info"""
    cur = conn.cursor()
    cur.execute(
        "SELECT `key`, `value` FROM vars WHERE `name`=%s AND `type`=%s", (name, 'h'))
    infos = {}
    for row in cur.fetchall():
        infos[row[0]] = row[1]
    cur.close()
    print json.dumps(infos, indent=4)


def print_help():
    """Print a short help"""
    print """Usage:
    {0} --list
    {0} --host [host]
    {0} --addhost [group] [host]
    {0} --addhostvar [host] [key] [value]
    {0} --addgroupvar [group] [key] [value]
    {0} --addchild [group] [child]
    {0} --delhost [group] [host]
    {0} --delgroupvar [group] [key]
    {0} --delhostvar [host] [key]
    {0} --delchild [group] [child]
    """.format(sys.argv[0])


# main execution
if __name__ == '__main__':
    con = MySQLdb.connect(host=server, port=server_port,
                          user=username, passwd=password, db=db_name)
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
                group_list(con)
        elif sys.argv[1] == "--host":
            if len(sys.argv) != 3:
                print "Usage: " + sys.argv[0] + " --host [host]"
            else:
                hostinfo(con, sys.argv[2])
        else:
            print_help()
    else:
        print_help()
    con.close()
