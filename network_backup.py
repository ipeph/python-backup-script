#!/var/venv/bin/python3.8

#####################################################
##### Backup Script
##### Created By
##### Febry Citra Prawira Negara - April 2022
#####################################################

# import python packages
import os
from datetime import datetime
import pexpect
import shutil
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    ReadTimeout
)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
import base64
import smtplib
import threading

# initiate global variable class
class init:
    def __init__(self):
        today = datetime.now()
        self.year = today.strftime("%Y")
        self.month = today.strftime("%m")
        self.abbmonth = today.strftime("%b")
        self.day = today.strftime("%d")
        self.time = today.strftime("%H:%M")
        self.status = ""
        self.total_devices = 0
        self.total_backup_success = 0
        self.total_backup_failed = 0
        file_credentials = "/home/svc_dummy/.credentials"
        self.file_log = "/home/svc_dummy/prod/company-asia-id-network-network-backup/logging"
        self.credentials = get_credentials(file_credentials)
        self.sw = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.nexus = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.asa = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.wlc = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.f5 = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.bluecoat = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }
        self.tanberg = {
            "total" : 0,
            "html" : "",
            "file" : ""
        }


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
    os.chown(fname, 540, 1000)

# count total inventory for threading
def count_total_inventory(*input):
    # open inventory file
    file = open(input[0], "r")
    # execute backup script
    for line in nonblank_lines(file):
        if not (line.startswith("#") or line.startswith(";")):
            _init.total_devices += 1

# backup function for all cisco devices
def backup_cisco(file, type, devtype):
    temp_count_inventory = _init.total_devices
    # open inventory file
    file_network_inventory = open(file, "r")
    # execute backup script
    for line in nonblank_lines(file_network_inventory):
        if not (line.startswith("#") or line.startswith(";")):
            if type == "cisco_ios":
                _init.sw["total"] += 1
            elif type == "cisco_nxos":
                _init.nexus["total"] += 1
            elif type == "cisco_asa":
                _init.asa["total"] += 1
            elif type == "cisco_wlc":
                _init.wlc["total"] += 1
            temp_count_inventory += 1
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
            file_status = "Checking device .... " + network_devices["ip"]
            # print("Checking device .... " + network_devices["ip"], end=" ", flush=True)
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
                    file_status += " ----> Backup Success\n"
                    class_status = "normal"
                    status = "Backup Success"
                    print("Checking device .... " + network_devices["ip"] + "----> Backup Success")
                    net_connect.disconnect()
                    _init.total_backup_success += 1
            except (NetmikoTimeoutException, ReadTimeout, NetmikoAuthenticationException) as error:
                write_file(network_devices["ip"], str(error))
                # print(error)
                file_status += " ----> Backup Failed\n"
                class_status = "error"
                status = "Backup Failed"
                print("Checking device .... " + network_devices["ip"] + " ----> Backup Failed")
                _init.total_backup_failed += 1
            # write backup summary to file
            temp_html(
                temp_count_inventory,
                network_devices["ip"],
                devtype,
                class_status,
                status,
                type
            )
            # write temp file status
            temp_file(
                type,
                file_status
            )
    # closing files
    file_network_inventory.close()


# backup function for all f5 devices
def backup_f5(file):
    temp_count_inventory = _init.total_devices
    # open inventory file
    file_network_inventory = open(file, "r")
    # execute backup script
    for line in nonblank_lines(file_network_inventory):
        if not (line.startswith("#") or line.startswith(";")):
            temp_count_inventory += 1
            _init.f5["total"] += 1
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
            file_status = "Checking device .... " + network_devices["ip"]
            # print("Checking device .... " + network_devices["ip"], end=" ", flush=True)
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
                    backup_file = "/tftpboot/{}/{}/{}/{}-{}.ucs".format(
                        _init.year,
                        _init.month,
                        _init.day,
                        network_devices["ip"],
                        _init.time,
                    )
                    touch(backup_file)
                    scp = pexpect.spawn(remote_file + " " + backup_file, timeout=60)
                    parent = scp.expect(["WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!","Password:","(yes/no)"])
                    if parent == 0:
                        os.system('rm -rf /home/svc_netbackup/.ssh/known_hosts')
                        scp.expect(pexpect.EOF)
                        scp = pexpect.spawn(remote_file + " " + backup_file, timeout=60)
                        parent = scp.expect(["Password:", "(yes/no)"])
                        if parent == 0:
                            scp.sendline(network_devices["password"])
                        else:
                            scp.sendline("yes")
                            scp.expect(["Password:"])
                            scp.sendline(network_devices["password"])
                    elif parent == 1:
                         scp.sendline(network_devices["password"])
                    else:
                        scp.sendline("yes")
                        scp.expect(["Password:"])
                        scp.sendline(network_devices["password"])
                    scp.expect(pexpect.EOF)
                    output = scp.before.decode("utf-8", "ignore")
                    write_file(_init.file_log + "/" + network_devices["ip"], output)
                    if "100%" in output:
                        file_status += " ----> Backup Success\n"
                        class_status = "normal"
                        status = "Backup Success"
                        print("Checking device .... " + network_devices["ip"] + "----> Backup Success")
                        _init.total_backup_success += 1
                    else:
                        file_status += " ----> Backup Failed\n"
                        class_status = "error"
                        status = "Backup Failed"
                        print("Checking device .... " + network_devices["ip"] + " ----> Backup Failed")
                        _init.total_backup_failed += 1
            except (NetmikoTimeoutException, ReadTimeout, NetmikoAuthenticationException) as error:
                write_file(network_devices["ip"], str(error))
                # print(error)
                file_status += " ----> Backup Failed\n"
                class_status = "error"
                status = "Backup Failed"
                print("Checking device .... " + network_devices["ip"] + " ----> Backup Failed")
                _init.total_backup_failed += 1
            # write temp html status
            temp_html(
                temp_count_inventory,
                network_devices["ip"],
                "F5",
                class_status,
                status,
                "f5_ltm"
            )
            # write temp file status
            temp_file(
                "f5_ltm",
                file_status
            )
    # closing files
    file_network_inventory.close()

# temporary html data for threading
def temp_html(*input):
    data = """<tr>
<td>{}</td>
<td>{}</td>
<td>{}</td>
<td class="{}">{}</td>
</tr>
""".format(
            input[0], input[1], input[2], input[3], input[4]
        )
    if input[5] == "cisco_ios":
        _init.sw["html"] += data
    elif input[5] == "cisco_nxos":
        _init.nexus["html"] += data
    elif input[5] == "cisco_asa":
        _init.asa["html"] += data
    elif input[5] == "cisco_wlc":
        _init.wlc["html"] += data
    elif input[5] == "f5_ltm":
        _init.f5["html"] += data

# temporary file data for threading
def temp_file(device, data):
    if device == "cisco_ios":
        _init.sw["file"] += data
    elif device == "cisco_nxos":
        _init.nexus["file"] += data
    elif device == "cisco_asa":
        _init.asa["file"] += data
    elif device == "cisco_wlc":
        _init.wlc["file"] += data
    elif device == "f5_ltm":
        _init.f5["file"] += data

# write report to html
def write_html(*input):
    if input[0] == "header":
        header = """<h3>Company - Indonesia Network Device Daily Backup Status</h3><h3>Daily Health Check - {}-{}-{} - {}</h3></td>
</tr>
<tr>
<div align="center"><td colspan=2 class="data">
<table class="data"><tr>
<th>No</th>
<th>Device Name</th>
<th>Device Type</th>
<th>Backup Status</th>
</tr>
""".format(
            _init.day, _init.abbmonth, _init.year, _init.time
        )
        file = open("/home/svc_dummy/prod/company-asia-id-network-network-backup/backup-report.html", "a")
        file.writelines(header)
        file.close()
    elif input[0] == "footer":
        footer = """</table>
<br \>
</div>
</td>
</tr>
<tr>
<td colspan=2 class=footer1>
<p style="font-weight: bold;">Total Statistics Backup:</p>
<ul>
<li>Total Network Devices : {}</li> 
<li>Total Successfully Backup  : {}</li>
<li>Total Failed Backup : {}</li>
</ul>
<p style="font-weight: bold;">Information:</p>
<ul>
<li><b style="color:red">See a Failed backup !!!</b></li>
<li>Don't hestitate to reach <b>SELF COMPANY &lt;<a href="mailto:self@company.com">self@company.com</a>></b>, our team will fix this issue shortly.</li>
</ul>
<p>Have any questions? You may reach out to <b>SELF COMPANY &lt;<a href="mailto:self@company.com">self@company.com</a>></b>.</p><p>Tech care, </p>
<p><b>SELF COMPANY</b></p>
</td>
</tr>
<tr>
<td colspan=2 class=footer2>
<p>Powered by Company | &#169; 2023</p>
</td>
</tr>
</table>
</div>
</body>
""".format(
            input[1],
            input[2],
            input[3],
        )
        file = open("/home/svc_dummy/prod/company-asia-id-network-network-backup/backup-report.html", "a")
        file.writelines(_init.sw["html"])
        file.writelines(_init.nexus["html"])
        file.writelines(_init.asa["html"])
        file.writelines(_init.wlc["html"])
        file.writelines(_init.f5["html"])
        file.writelines(footer)
        file.close()

# write configuration or exception to file
def write_file(filename, output):
    # write file backup_status
    if "backup-status" in filename:
        file = open("/tftpboot/{}/{}/{}".format(_init.year, _init.month, filename), "w")
        output += """#####
Total Devices:{}
Total Success:{}
Total Failed:{}
""".format(
            _init.total_devices, _init.total_backup_success, _init.total_backup_failed
        )
        file.writelines(_init.sw["file"])
        file.writelines(_init.nexus["file"])
        file.writelines(_init.asa["file"])
        file.writelines(_init.wlc["file"])
        file.writelines(_init.f5["file"])
        file.writelines(output)
        file.close()
        os.chmod(
            "/tftpboot/{}/{}/{}".format(_init.year, _init.month, filename), 0o644)
        os.chown(
            "/tftpboot/{}/{}/{}".format(_init.year, _init.month, filename), 540, 1000
        )
    elif "total-inventory" in filename:
        file = open("/home/svc_dummy/prod/company-asia-id-network-network-backup/total-inventory", "w")
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
Total Tanberg:{}
""".format(
            _init.sw["total"],
            _init.nexus["total"],
            _init.asa["total"],
            _init.wlc["total"],
            _init.f5["total"],
            _init.bluecoat["total"],
            _init.tanberg["total"],
        )
        file.writelines(output)
        file.close()
        os.chmod("/home/svc_dummy/prod/company-asia-id-network-network-backup/total-inventory", 0o644)
        os.chown("/home/svc_dummy/prod/company-asia-id-network-network-backup/total-inventory", 540, 1000)
    # write logging file
    elif "logging" in filename:
        file = open(filename, "a")
        file.writelines(output)
        file.close()
        os.chmod(filename, 0o644)
        os.chown(filename, 540, 1000)
    # write configuration file
    else:
        file = open(
            "/tftpboot/{}/{}/{}/{}-{}".format(
                _init.year, _init.month, _init.day, filename, _init.time
            ),
            "w",
        )
        file.writelines(output)
        file.close()
        os.chmod(
            "/tftpboot/{}/{}/{}/{}-{}".format(
                _init.year, _init.month, _init.day, filename, _init.time
            ),
            0o644,
        )
        os.chown(
            "/tftpboot/{}/{}/{}/{}-{}".format(
                _init.year, _init.month, _init.day, filename, _init.time
            ),
            540,
            1000,
        )

# send email report function
def email():

    # define variable address
    fromaddr = "SELF GO Network Automation <self@company.com>"
    toaddr = "nccindia@SELF.com"
    cc = "apsd.gndc.in@capgemini.com,self@company.com"
    recipient = cc.split(",") + [toaddr]
    
    # define message
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "ID - Network Device Daily Backup Report ({}-{}-{} - {})".format(_init.day, _init.abbmonth, _init.year, _init.time)
    msg['Cc'] = cc

    # replace image in HTML report
    encoded = base64.b64encode(open("/home/svc_dummy/prod/company-asia-id-network-network-backup/ago.png", "rb").read()).decode()
    with open('/home/svc_dummy/prod/company-asia-id-network-network-backup/backup-report.html', 'r') as file:
        html = file.read().replace('encoded', encoded)

    # define attachment using html
    part = MIMEText(html, 'html')
    # insert encoded picture into html
    encoders.encode_base64(part)

    # attach all into message
    msg.attach(part)

    # define SMTP server and send the email
    server = smtplib.SMTP('10.55.9.9', 25)

    # for debug purposes
    # server.set_debuglevel(2)
    
    server.sendmail(fromaddr, recipient, msg.as_string())
    server.quit()

def main():
    # remove current users mask
    os.umask(0)
    # remove existing backup folder
    shutil.rmtree(
        "/tftpboot/{}/{}/{}".format(_init.year, _init.month, _init.day), ignore_errors=True
    )
    # create backup and logging folder
    os.makedirs(
        "/tftpboot/{}/{}/{}".format(_init.year, _init.month, _init.day),
        mode=0o750,
        exist_ok=True,
    )
    os.chown("/tftpboot/{}/{}/{}".format(_init.year, _init.month, _init.day), 540, 1000)
    os.makedirs(_init.file_log, mode=0o750, exist_ok=True)
    os.chown(_init.file_log, 540, 1000)

    # copy report template
    os.system(
        "cp /home/svc_dummy/prod/company-asia-id-network-network-backup/backup-report-template.html /home/svc_dummy/prod/company-asia-id-network-network-backup/backup-report.html"
    )

    # write hml report header
    write_html("header")

    # cisco switch backup
    switch = "/home/svc_dummy/prod/company-asia-id-network-network-backup/inventory-switch"
    process_switch = threading.Thread(target=backup_cisco, args=(switch, "cisco_ios", "Cisco Switch",))
    process_switch.start()
    count_switch = threading.Thread(target=count_total_inventory, args=(switch,))
    count_switch.start()
    count_switch.join()

    # nexus switch backup
    nexus = "/home/svc_dummy/prod/company-asia-id-network-network-backup/inventory-nexus"
    process_nexus = threading.Thread(target=backup_cisco, args=(nexus, "cisco_nxos", "Cisco Nexus",))
    process_nexus.start()
    count_nexus = threading.Thread(target=count_total_inventory, args=(nexus,))
    count_nexus.start()
    count_nexus.join()

    # asa backup
    asa = "/home/svc_dummy/prod/company-asia-id-network-network-backup/inventory-asa"
    process_asa = threading.Thread(target=backup_cisco, args=(asa, "cisco_asa", "Cisco ASA",))
    process_asa.start()
    count_asa = threading.Thread(target=count_total_inventory, args=(asa,))
    count_asa.start()
    count_asa.join()

    # wlc backup
    wlc = "/home/svc_dummy/prod/company-asia-id-network-network-backup/inventory-wlc"
    process_wlc = threading.Thread(target=backup_cisco, args=(wlc, "cisco_wlc", "Cisco WLC",))
    process_wlc.start()
    count_wlc = threading.Thread(target=count_total_inventory, args=(wlc,))
    count_wlc.start()
    count_wlc.join()

    # f5 backup
    f5 = "/home/svc_dummy/prod/company-asia-id-network-network-backup/inventory-f5"
    process_f5 = threading.Thread(target=backup_f5, args=(f5,))
    process_f5.start()
    count_f5 = threading.Thread(target=count_total_inventory, args=(f5,))
    count_f5.start()
    count_f5.join()

    # wait till all thread finished executed
    process_switch.join()
    process_nexus.join()
    process_asa.join()
    process_wlc.join()
    process_f5.join()


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

    # write hml report footer
    write_html(
        "footer",
        _init.total_devices,
        _init.total_backup_success,
        _init.total_backup_failed,
    )

    # send email
    email()

# execute main program
if __name__ == "__main__":

    # initiate global variable
    _init = init()

    # execute main program
    main()
