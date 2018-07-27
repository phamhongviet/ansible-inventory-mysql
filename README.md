ansible-inventory-mysql
=======================

Simple Python script to manage Ansible inventory in mySQL

# Requirement
* Python 2.7 or Python >= 3.4
* PyMySQL

# How to use

## Setup

### Database

Create a mySQL database and user, `ansible_inv` and `ans` for example.

```
CREATE DATABASE ansible_inv;
GRANT ALL PRIVILEGES ON ansible_inv.* TO 'ans'@'localhost' IDENTIFIED BY '123123';
FLUSH PRIVILEGES;
QUIT;
```

```
mysql -u ans -p123123 ansible_inv < inv.sql
```

### Configuration

Provide database information in config file, for example:

```
[db]
server = localhost
port = 3306
name = ansible_inv
user = ans
password = 123123
```

The config file can be read from these location, whichever come first:
* Environment variable ANSIBLE_INV_CONFIG. Example:

```
ANSIBLE_INV_CONFIG=path/to/my-config.ini ansible -i path/to/inv.py -m ping all
```

* config.ini file in the same directory as inv.py file      
* config.ini file in the current directory      


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

## Example

Consider the following static inventory file:

```
[dc0:children]
web
db

[web]
w0 ansible_host=192.168.1.10
w1 ansible_host=192.168.1.11 ansible_user=ken

[web:vars]
ntp_servers=ntp0.example.com

[db]
db0 ansible_host=192.168.2.15
```

We can create the same inventory with these commands:

```
./inv.py --addchild dc0 web
./inv.py --addchild dc0 db

./inv.py --addhost web w0
./inv.py --addhostvar w0 ansible_host 192.168.1.10

./inv.py --addhost web w1
./inv.py --addhostvar w1 ansible_host 192.168.1.11
./inv.py --addhostvar w1 ansible_user ken

./inv.py --addgroupvar web ntp_servers ntp0.example.com

./inv.py --addhost db db0
./inv.py --addhostvar db0 ansible_host 192.168.2.15
```

You can try to ping the hosts with:

```
ansible -i inv.py -m ping all
```

# Reference
[Working With Dynamic Inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_dynamic_inventory.html)
