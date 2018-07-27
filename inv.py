#!/usr/bin/env python
"""ansible-inventory-mysql: Manage Ansible inventory using MySQL compabitible database"""

import sys
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import MySQLdb
import os
try:
    import json
except ImportError:
    import simplejson as json


class AnsibleInventoryMySQL:
    """Manage Ansible inventory using MySQL compabitible database"""

    def __init__(self, db_server='localhost', db_port=3306, db_name='ansible_inv', db_user='ans', db_password='123123'):
        self.db_server = db_server
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password

    def connect(self):
        self.connection = MySQLdb.connect(host=self.db_server, port=self.db_port,
                                          user=self.db_user, passwd=self.db_password, db=self.db_name)

    def group_list(self):
        """Create a JSON list of hosts to work with Ansible"""
        inventory = {}
        cur = self.connection.cursor()
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
        print(json.dumps(inventory, indent=4))

    def add(self, group, name, type):
        """Add a host or child to inventory, safely ignore if host or child exists"""
        cur = self.connection.cursor()
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
            self.connection.commit()
        cur.close()

    def delete(self, group, name, type):
        """Delete host(s) or child(ren) from inventory"""
        cur = self.connection.cursor()
        cur.execute(
            "DELETE FROM groups WHERE `group`=%s AND `name`=%s AND `type`=%s",
            (group,
             name,
             type))
        self.connection.commit()
        cur.close()

    def add_var(self, name, type, key, value):
        """Add host/group vars to inventory, safely ignore if exists"""
        cur = self.connection.cursor()
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
            self.connection.commit()
        else:
            cur.execute(
                "UPDATE vars SET `value`=%s WHERE `name`=%s AND `type`=%s AND `key`=%s",
                (value,
                 name,
                 type,
                 key))
            self.connection.commit()
        cur.close()

    def del_var(self, name, type, key):
        """Delete host or group vars from inventory"""
        cur = self.connection.cursor()
        if key is None:
            cur.execute(
                "DELETE FROM vars WHERE `name`=%s AND `type`=%s", (name, type))
            self.connection.commit()
        else:
            cur.execute(
                "DELETE FROM vars WHERE `name`=%s AND `type`=%s AND `key`=%s",
                (name,
                 type,
                 key))
            self.connection.commit()
        cur.close()

    def host_info(self, name):
        """Return host info"""
        cur = self.connection.cursor()
        cur.execute(
            "SELECT `key`, `value` FROM vars WHERE `name`=%s AND `type`=%s", (name, 'h'))
        infos = {}
        for row in cur.fetchall():
            infos[row[0]] = row[1]
        cur.close()
        print(json.dumps(infos, indent=4))

    def print_help(self):
        """Print a short help"""
        print("""Usage:
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
        """.format(sys.argv[0]))


def main():

    config_file_list = list()
    try:
        config_file_list.append(os.environ["ANSIBLE_INV_CONFIG"])
    except KeyError:
        pass
    config_file_list.append(
        "{}/{}".format(os.path.dirname(sys.argv[0]), "config.ini"))
    config_file_list.append("config.ini")

    config_file = config_file_list[-1]
    for potential_config_file in config_file_list:
        if os.path.isfile(potential_config_file):
            config_file = potential_config_file
            break

    default_config = {
        "server": "localhost",
        "port": 3306,
        "name": "ansible_inv",
        "user": "ans",
        "password": "123123"
    }
    config = configparser.RawConfigParser(default_config)
    config.read(config_file)

    try:
        db_server = config.get("db", "server")
        db_port = config.get("db", "port")
        db_name = config.get("db", "name")
        db_user = config.get("db", "user")
        db_password = config.get("db", "password")
        inv = AnsibleInventoryMySQL(db_server, db_port, db_name, db_user, db_password)
    except configparser.NoSectionError:
        inv = AnsibleInventoryMySQL()

    inv.connect()
    if len(sys.argv) > 1:
        if sys.argv[1] == "--addhost":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --addhost [group] [host]")
            else:
                inv.add(sys.argv[2], sys.argv[3], 'h')
        elif sys.argv[1] == "--addchild":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --addchild [group] [child]")
            else:
                inv.add(sys.argv[2], sys.argv[3], 'c')
        elif sys.argv[1] == "--addhostvar":
            if len(sys.argv) != 5:
                print("Usage: " + sys.argv[0] + " --addhostvar [host] [key] [value]")
            else:
                inv.add_var(sys.argv[2], 'h', sys.argv[3], sys.argv[4])
        elif sys.argv[1] == "--addgroupvar":
            if len(sys.argv) != 5:
                print("Usage: " + sys.argv[0] + " --addgroupvar [group] [key] [value]")
            else:
                inv.add_var(sys.argv[2], 'g', sys.argv[3], sys.argv[4])
        elif sys.argv[1] == "--delhost":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --delhost [group] [host]")
            else:
                inv.del_var(sys.argv[3], 'h', None)
                inv.delete(sys.argv[2], sys.argv[3], 'h')
        elif sys.argv[1] == "--delchild":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --delchild [group] [child]")
            else:
                inv.delete(sys.argv[2], sys.argv[3], 'c')
        elif sys.argv[1] == "--delhostvar":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --delhostvar [host] [key]")
            else:
                inv.del_var(sys.argv[2], 'h', sys.argv[3])
        elif sys.argv[1] == "--delgroupvar":
            if len(sys.argv) != 4:
                print("Usage: " + sys.argv[0] + " --delgroupvar [group] [key]")
            else:
                inv.del_var(sys.argv[2], 'g', sys.argv[3])
        elif sys.argv[1] == "--list":
            if len(sys.argv) != 2:
                print("Usage: " + sys.argv[0] + " --host [host]")
            else:
                inv.group_list()
        elif sys.argv[1] == "--host":
            if len(sys.argv) != 3:
                print("Usage: " + sys.argv[0] + " --host [host]")
            else:
                inv.host_info(sys.argv[2])
        else:
            inv.print_help()
    else:
        inv.print_help()
    inv.connection.close()


if __name__ == "__main__":
    main()
