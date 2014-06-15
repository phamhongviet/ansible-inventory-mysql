ansible-inventory-mysql
=======================

Simple Python script to manage Ansible inventory in mySQL

# Requirement
* Python 2.7
* MySQLdb

# How to use

## Setup

* Create a mySQL database and user, `ansible_inv` and `ans` for example.

```
mysql> CREATE DATABASE ansible_inv;
mysql> GRANT ALL PRIVILEGES ON ansible_inv.* TO 'ans'@'localhost' IDENTIFIED BY '123123';
mysql> FLUSH PRIVILEGES;
mysql> QUIT
```

`mysql -u ans -p123123 ansible_inv < inv.sql`

* Provide database information

```
server = 'localhost'
db_name = 'ansible_inv'
username = 'ans'
password = '123123'
```

## Commands

`--list`: print out inventory information

`--host [host]`: print out host information

`--addhost [group] [host]`: add a new host, and a new group if necessary

`--addhostvar [host] [key] [value]`: add a host variable

`--addgroupvar [group] [key] [value]`: add a group variable

`--addchild [group] [child]`: add a group child

`--delhost [group] [host]`: delete a host, empty group will be deleted

`--delhostvar [host] [key]`: delete a host variable

`--delgroupvar [group] [key]`: delete a group variable

`--delchild [group] [child]`: delete a group child
