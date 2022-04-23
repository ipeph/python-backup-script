# Python Backup Script
## by Febry

This backup script mostly written by python.

- ✨Backup✨

## Features

- Backup Cisco ASA, Switch, Nexus, WLC
- Backup F5, Bluecoat, Tanberg
- Backup based on Date
- Added logging to track backup status or process

## Prerequisite

This backup script requires [python-3.6 ++](https://www.python.org/downloads/release/python-380/) to run.

Install the dependencies.

```py
pip3 install -U netmiko --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user
pip3 install -U pexpect --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user
```

or

```sh
python3 -m pip install -U netmiko --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user
python3 -m pip install -U pexpect --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --user
```

## How to use

Make sure you edit .credentials (credentials to login the devices)
Change your `username` and `password` on .credentials file

Make sure you edit network_backup.py (backup configuration)
Change `/path-to-your` to your windows or linux directory

Make sure you edit inventory file

Inventory can be :

```sh
devices
devices:username:password
```

If you only mentioned device it will use username/password on .credentials file.
If you put : it will use local credentials.

Tree file

 * network_backup.py
 * inventory-asa 
 * inventory-f5
 * inventory-nexus
 * inventory-switch
 * inventory-wlc
 * inventory-bluecoat
 * inventory-tanberg
 * backup
   * backup file 1
   * backup file 2
   * backup file 3
 * logging
   * backup logging process file1
   * backup logging process file2
   * backup logging process file3

## Execution
To execute the program, just enter this on your linux machine.

```sh
chmod +x network_backup.py
./network_backup.py
```

## Integration with Crontab
You can schedule this script using crontab to run every day at 1 AM example

```sh
crontab -e
```

Edit crontab file
```
### run daily backup ###
0 1 * * * /path-to-your/backup/network_backup.py > /dev/null 2>&1
```

## License

**Free Software, Hell Yeah!**
