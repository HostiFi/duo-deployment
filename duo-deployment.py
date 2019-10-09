import paramiko
import MySQLdb
import time
import string
import random

def pw_gen(size=16, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

file_already_done = open('/home/hostifi/duo_already_done.txt', 'r')
list_already_done = [line.rstrip('\n') for line in file_already_done.readlines()]

# Open database connection
db = MySQLdb.connect("localhost","user","password","db" )
cursor = db.cursor()
sql = "SELECT * FROM vultr_servers"
vultr_servers = []
try:
    # Execute the SQL command
    cursor.execute(sql)
    results = cursor.fetchall()
    for row in results:
        vultr_servers.append(row[6])
  
except Exception as e:
    print "Error: " + str(e)

servers = []
for server_1 in vultr_servers:
    skip_it = 0
    for server_2 in list_already_done:
        if server_2 == server_1:
            skip_it = 1
    if skip_it == 0:
        servers.append(server_1)
print servers
for server in servers:
    k = paramiko.RSAKey.from_private_key_file("private_key.pem", password="abc")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    times_tried = 0
    while times_tried < 10:
        try:
            c.connect(hostname=server, username="root", pkey=k)
            break
        except Exception as e:
            print e
            times_tried += 1
            print "Try again .."
    command = 'wc -l < /root/.ssh/authorized_keys'
    print "Executing {}".format(command)
    stdin, stdout, stderr = c.exec_command(command)
    try:
        number_of_keys = int(stdout.read())
    except:
        number_of_keys = 0
    print "Number of keys"
    print number_of_keys
    if number_of_keys == 2:
        outF = open("/home/hostifi/duo_already_done.txt", "a")
        outF.write(server)
        outF.write("\n")
        outF.close()
    else:
        outF = open("/home/hostifi/duo_already_done.txt", "a")
        outF.write(server)
        outF.write("\n")
        outF.close()

        outF = open("/home/hostifi/duo_needs_fixed.txt", "a")
        outF.write(server)
        outF.write("\n")
        outF.close()
    random_pw = pw_gen()
    commands = [
        "echo 'unifi:" + random_pw + "' | chpasswd",
        "echo 'deb https://pkg.duosecurity.com/Debian stretch main' > /etc/apt/sources.list.d/duosecurity.list",
        "curl -s https://duo.com/APT-GPG-KEY-DUO | apt-key add -",
        "apt-get install apt-transport-https -y",
        "apt-get update -y && apt-get install duo-unix -y",
        """cat <<EOM >/etc/duo/login_duo.conf
[duo]
; Duo integration key
ikey = abc
; Duo secret key
skey = abc
; Duo API host
host = api-abc.duosecurity.com
; `failmode = safe` In the event of errors with this configuration file or connection to the Duo service
; this mode will allow login without 2FA.
; `failmode = secure` This mode will deny access in the above cases. Misconfigurations with this setting
; enabled may result in you being locked out of your system.
failmode = secure
; Send command for Duo Push authentication
; pushinfo = yes
prompts=1
autopush=yes
EOM""",
        "mv /root/.ssh/authorized_keys /root/.ssh/authorized_keys.old",
        "touch /root/.ssh/authorized_keys",
        "chmod 700 /root/.ssh",
        "echo 'command=\"/usr/sbin/login_duo -f user1\" ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAoVhyZrVzuGTD8xzix9MIo/e+oavootpICIQHGZsMUR8PgJNetmMm89KXSiXGIKCgBGVttsR6U024SsQWKqOZ9M1+FrhJR/QOTyq8M1s3gJt2W9Y4sxWVOyIfyF2wdLgwv770cuilOU6h/CVD3Aq+/a+YT3geS6PfBYEKafAjQhpF+5k7xX/Gndp/I9pjynoDOE+D1A3QhQsotC9P+PdT5mXG1lK9sRyWseH96nGqjjqBGBk7Lm7lx3ZWptseGue8sZQDwDOdO4fEtWJGgFe7FGsym9TdtMTX1qq0Mdp7S6ZxgiI9dYzHgbA/3i7px/doLxPLyuEAE8L1JFtvraAvYw== user1@example.com' >> /root/.ssh/authorized_keys",
        "echo 'command=\"/usr/sbin/login_duo -f user2\" ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAjVttM1Fv9wtvBxitlm/C1jtI4PRAcOdXCUEnraxcbbUdeEXy9DmVr2bh1IyrBp7x8A1as1nsuNW6CTxHFdCDUDfjCnWBxQ8uro1rityA/EfqKNVwzMsKqcFx8fNAuq9axjl6LvveVtmnrPWqqI4XDWFn2rIKvUESFw1iRMTl3lG8V8MPtogUoYOJDKxUEuEKIWO5ELw7zsZgaigIVkvXnDPo87nwTStRQo69+M6/h+3zsuyA/3n+ZPA3oSBpAEhaWZ63NL16ajc/r++//1rpLq1eCR/rrY9Lwa49JzVwfxwJay9MXmYEhx8T9dXxc5NW6q7SZdqhW3ySZR/I052w/w== user2@example.com' >> /root/.ssh/authorized_keys",
        "echo 'command=\"/usr/sbin/login_duo -f user3\" ssh-rsa AAAAB3NzaC1yc2EAAAABJQAAAQEAllk8FTdPnmxChUJyE/KV5tVvoUmLgJksVxJ/7Y5tEm3N8Az5WoXGflGOeUD9y6RWI17VQnmb9tDOdX8e1+4yiSch23hl1u54+UmXSdFqUiXrKJQbsWzq9USoJM/hG+2NU8bTu6z+6dfBD8AHnWgkLKckZ13fe6CNiGFOJ1ifXGmL+XJ1tpURWnTjA2xT+QzXnHLsZWKHZjr+uQtrdPxCIZrZ4LDFls6wkBGoZni7AQ19Df6hTfSuAyW9a/iCJ3sg7/tLAuY8o0/kRISF6mb9/iW/Hql9FUOJoq3d+liYYqJ1JAF/F7RhchadvUebvQhBteiVuFfBqpuYh9AtsB4ctQ== user3@example.com' >> /root/.ssh/authorized_keys",
        "echo 'PermitTunnel no' >> /etc/ssh/sshd_config",
        "echo 'AllowTcpForwarding no' >> /etc/ssh/sshd_config",
        "service sshd restart",
        "service ssh restart"
        ]
    for command in commands:
        print command
        print "Executing {}".format(command)
        stdin, stdout, stderr = c.exec_command(command)
        print stdout.read()
        print stderr.read()
        time.sleep(2)
    c.close()
