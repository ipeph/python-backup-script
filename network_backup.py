#!/var/venv/bin/python3.8

#####################################################
##### Network Backup Script
##### Created By
##### Febry Citra Prawira Negara - April 2022
#####################################################

# import python packages
import os
from datetime import datetime
import pexpect
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

# initiate global variable class
class init:
    def __init__(self):
        today = datetime.now()
        self.year = today.strftime("%Y")
        self.month = today.strftime("%m")
        self.day = today.strftime("%d")
        self.time = today.strftime("%H%M")
        self.status = ""
        self.total_devices = 0
        self.total_backup_success = 0
        self.total_backup_failed = 0
        file_credentials = "/path-to-your/.credentials"
        self.file_log = "/path-to-your/backup/logging"
        self.credentials = get_credentials(file_credentials)
        self.sw = 0
        self.nexus = 0
        self.asa = 0
        self.wlc = 0
        self.f5 = 0
        self.bluecoat = 0
        self.tandberg = 0


# define function
# devices dictionary
def network_connection_ip(*input):
    # type, hostname, username, password, fastcli, log
    return {
        "device_type": input[0],
        "ip": input[1],
        "username": input[2],
        "password": input[3],
        "secret": input[3],
        "fast_cli": input[4],
        "session_log": input[5] + "/" + input[1],
    }


# define credentials
def get_credentials(file):
    credentials = {}
    try:
        with open(file) as file_credentials:
            file_credentials = open(file)
            for line in file_credentials:
                key, value = line.split()
                credentials[key] = value
            file_credentials.close()
            return credentials
    # flush exception if file not found
    except FileNotFoundError as e:
        print(
            "{}\n{}".format(
                str(e),
                "Please create base username and password on your local directory and saved it as .credentials",
            )
        )
        quit()


# removed newlines when reading file
def nonblank_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield line


# create new filename
def touch(fname):
    if os.path.exists(fname):
        os.utime(fname, None)
    else:
        open(fname, "a").close()


# write configuration or exception to file
def write_file(filename, output):
    # write file backup_status
    if "backup-status" in filename:
        file = open("/path-to-your/backup/backup/{}/{}/{}".format(_init.year, _init.month, filename), "w")
        output += """#####
Total Devices:{}
Total Success:{}
Total Failed:{}
""".format(
            _init.total_devices, _init.total_backup_success, _init.total_backup_failed
        )
        file.writelines(output)
        file.close()
        os.chmod("/path-to-your/backup/backup/{}/{}/{}".format(_init.year, _init.month, filename), 0o644)
    elif "total-inventory" in filename:
        file = open("/path-to-your/backup/total-inventory", "w")
        output = """###########################
### FILE AUTO GENERATED ###
### DON'T EDIT THE FILE ###
###########################
Total Switch:{}
Total Nexus:{}
Total ASA:{}
Total WLC:{}
Total F5:{}
Total Bluecoat:{}
Total Tandberg:{}
""".format(
            _init.sw,
            _init.nexus,
            _init.asa,
            _init.wlc,
            _init.f5,
            _init.bluecoat,
            _init.tandberg,
        )
        file.writelines(output)
        file.close()
        os.chmod("/path-to-your/backup/total-inventory", 0o644)
    # write logging file
    elif "logging" in filename:
        file = open(filename, "a")
        file.writelines(output)
        file.close()
        os.chmod(filename, 0o644)
    # write configuration file
    else:
        file = open(
            "/path-to-your/backup/backup/{}/{}/{}/{}-{}".format(
                _init.year, _init.month, _init.day, filename, _init.time
            ),
            "w",
        )
        file.writelines(output)
        file.close()
        os.chmod(
            "/path-to-your/backup/backup/{}/{}/{}/{}-{}".format(
                _init.year, _init.month, _init.day, filename, _init.time
            ),
            0o644,
        )


# backup function for all cisco devices
def backup_cisco(file, type):
    # open inventory file
    file_network_inventory = open(file, "r")
    # execute backup script
    for line in nonblank_lines(file_network_inventory):
        if not (line.startswith("#") or line.startswith(";")):
            if type == "cisco_ios":
                _init.sw += 1
            elif type == "cisco_nxos":
                _init.nexus += 1
            elif type == "cisco_asa":
                _init.asa += 1
            elif type == "cisco_wlc":
                _init.wlc += 1
            _init.total_devices += 1
            param = line.split(":")
            if len(param) == 3:
                network_devices = network_connection_ip(
                    type, param[0], param[1], param[2], True, _init.file_log
                )
            else:
                network_devices = network_connection_ip(
                    type,
                    line.strip(),
                    _init.credentials["username"],
                    _init.credentials["password"],
                    True,
                    _init.file_log,
                )
            _init.status += "Checking device .... " + network_devices["ip"]
            print("Checking device .... " + network_devices["ip"], end=" ", flush=True)
            try:
                with ConnectHandler(**network_devices) as net_connect:
                    if type == "cisco_wlc":
                        output = net_connect.send_command(
                            "show run-config commands", read_timeout=120
                        )
                    else:
                        if not net_connect.check_enable_mode():
                            net_connect.enable()
                        output = net_connect.send_command(
                            "show running-config", read_timeout=120
                        )
                    # print (output)
                    write_file(network_devices["ip"], output)
                    _init.status += " ----> Backup Success\n"
                    print(" ----> Backup Success")
                    net_connect.disconnect()
                    _init.total_backup_success += 1
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
                write_file(network_devices["ip"], str(error))
                # print(error)
                _init.status += " ----> Backup Failed\n"
                print(" ----> Backup Failed")
                _init.total_backup_failed += 1
    # closing files
    file_network_inventory.close()


# backup function for all f5 devices
def backup_f5(file):
    # open inventory file
    file_network_inventory = open(file, "r")
    # execute backup script
    for line in nonblank_lines(file_network_inventory):
        if not (line.startswith("#") or line.startswith(";")):
            _init.total_devices += 1
            _init.f5 += 1
            param = line.split(":")
            if len(param) == 3:
                network_devices = network_connection_ip(
                    "f5_ltm", param[0], param[1], param[2], False, _init.file_log
                )
            else:
                network_devices = network_connection_ip(
                    "f5_ltm",
                    line.strip(),
                    _init.credentials["username"],
                    _init.credentials["password"],
                    False,
                    _init.file_log,
                )
            _init.status += "Checking device .... " + network_devices["ip"]
            print("Checking device .... " + network_devices["ip"], end=" ", flush=True)
            try:
                with ConnectHandler(**network_devices) as net_connect:
                    output = net_connect.send_command_timing(
                        "save /sys ucs /var/local/ucs/" + network_devices["ip"],
                        read_timeout=600,
                        strip_prompt=False,
                        strip_command=False,
                    )
                    if "(y/n)" in output:
                        output += net_connect.send_command_timing(
                            "y",
                            read_timeout=600,
                            strip_prompt=False,
                            strip_command=False,
                        )
                    if "#" in output:
                        output = net_connect.send_command_timing("quit")
                    # print (output)
                    net_connect.disconnect()
                    # begin transfer configuration file
                    remote_file = "scp {}@{}:/var/local/ucs/{}.ucs ".format(
                        network_devices["username"],
                        network_devices["ip"],
                        network_devices["ip"],
                    )
                    backup_file = "/path-to-your/backup/backup/{}/{}/{}/{}-{}.ucs".format(
                        _init.year,
                        _init.month,
                        _init.day,
                        network_devices["ip"],
                        _init.time,
                    )
                    touch(backup_file)
                    scp = pexpect.spawn(remote_file + " " + backup_file, timeout=60)
                    parent = scp.expect(["Password:", "(yes/no)"])
                    if parent == 0:
                        scp.sendline(network_devices["password"])
                    else:
                        scp.sendline("yes")
                        scp.expect(["Password:"])
                        scp.sendline(network_devices["password"])
                    scp.expect(pexpect.EOF)
                    output = scp.before.decode("utf-8", "ignore")
                    write_file(_init.file_log + "/" + network_devices["ip"], output)
                    if "100%" in output:
                        _init.status += " ----> Backup Success\n"
                        print(" ----> Backup Success")
                        _init.total_backup_success += 1
                    else:
                        _init.status += " ----> Backup Failed\n"
                        print(" ----> Backup Failed")
                        _init.total_backup_failed += 1
            except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
                write_file(network_devices["ip"], str(error))
                # print(error)
                _init.status += " ----> Backup Failed\n"
                print(" ----> Backup Failed")
                _init.total_backup_failed += 1
    # closing files
    file_network_inventory.close()


def main():
    # remove current users mask
    os.umask(0)
    # create backup and logging folder
    os.makedirs(
        "/path-to-your/backup/backup/{}/{}/{}".format(_init.year, _init.month, _init.day),
        mode=0o750,
        exist_ok=True,
    )
    os.makedirs(_init.file_log, mode=0o750, exist_ok=True)

    # cisco switch backup
    backup_cisco(
        "/path-to-your/backup/inventory-switch", "cisco_ios"
    )

    # nexus switch backup
    backup_cisco(
        "/path-to-your/backup/inventory-nexus", "cisco_nxos"
    )

    # asa backup
    backup_cisco("/path-to-your/backup/inventory-asa", "cisco_asa")

    # wlc backup
    backup_cisco("/path-to-your/backup/inventory-wlc", "cisco_wlc")

    # f5 backup
    backup_f5("/path-to-your/backup/inventory-f5")

    # write backup _init.status to file
    write_file(
        "backup-status-{}.{}.{}".format(_init.year, _init.month, _init.day),
        _init.status,
    )

    # write total inventory to file
    write_file(
        "total-inventory",
        "",
    )


# execute main program
if __name__ == "__main__":

    # initiate global variable
    _init = init()

    # execute main program
    main()
