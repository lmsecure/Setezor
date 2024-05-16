
# Скан cnmp с NMAP

Этот документ создан, чтобы были примеры cnmp, а также возможные варианты ответа. На данный момент парсится все ниже перечисленное, кроме **snmp-w32-software**.
Взято из https://medium.com/@minimalist.ascent/enumerating-snmp-servers-with-nmap-89aaf33bce28

`nmap -sU -p 161 -sC <target>`

Параметры
- `-sU` скан по udp
- `-sC` сбор всей информации по snmp

Можно запускать и отдельные сканы, примеры:

 - snmp-info
```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-info 192.168.0.25Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:32 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.00042s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-info: 
|   enterprise: net-snmp
|   engineIDFormat: unknown
|   engineIDData: 5fd4fd7eafbcbf5c00000000
|   snmpEngineBoots: 4
|_  snmpEngineTime: 2d21h31m42sNmap done: 1 IP address (1 host up) scanned in 2.29 seconds
root@asus:~/unix%
```

- snmp-interfaces
```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-interfaces 192.168.0.25Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:33 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.00053s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-interfaces: 
|   lo
|     IP address: 192.168.0.25  Netmask: 255.0.0.0
|     Type: softwareLoopback  Speed: 10 Mbps
|     Status: up
|     Traffic stats: 33.45 Mb sent, 33.45 Mb received
|   Intel Corporation Wireless 7265
|     IP address: 10.228.100.110  Netmask: 255.224.0.0
|     MAC address: f8:94:c2:f6:72:64 (Unknown)
|     Type: ethernetCsmacd  Speed: 0 Kbps
|     Status: up
|_    Traffic stats: 1.55 Gb sent, 1.41 Gb receivedNmap done: 1 IP address (1 host up) scanned in 1.49 seconds
root@asus:~/unix%
```

- snmp-netstat
```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-netstat 192.168.0.25Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:33 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.00044s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-netstat: 
|   TCP  0.0.0.0:389          0.0.0.0:0
|   TCP  0.0.0.0:4433         0.0.0.0:0
|   TCP  0.0.0.0:58210        0.0.0.0:0
|   TCP  10.228.100.110:39722 184.25.204.33:80
|   TCP  10.228.100.110:47888 172.217.1.206:443
|   TCP  10.228.100.110:48270 172.217.1.206:443
|   TCP  10.228.100.110:53402 74.125.201.188:5228
|   TCP  10.228.100.110:58136 173.194.162.170:443
|   TCP  10.228.100.110:59808 74.125.1.169:443
|   TCP  10.228.100.110:59814 74.125.1.169:443
|   TCP  192.168.0.25:631        0.0.0.0:0
|   TCP  192.168.0.25:3306       0.0.0.0:0
|   TCP  192.168.0.25:6667       0.0.0.0:0
|   UDP  0.0.0.0:68           *:*
|   UDP  0.0.0.0:123          *:*
|   UDP  0.0.0.0:161          *:*
|   UDP  0.0.0.0:631          *:*
|   UDP  0.0.0.0:5353         *:*
|   UDP  0.0.0.0:6771         *:*
|   UDP  0.0.0.0:35616        *:*
|   UDP  0.0.0.0:35686        *:*
|   UDP  0.0.0.0:42840        *:*
|   UDP  0.0.0.0:58210        *:*
|   UDP  0.0.0.0:58338        *:*
|   UDP  10.228.100.110:123   *:*
|   UDP  10.228.100.110:6771  *:*
|   UDP  10.228.100.110:37725 *:*
|   UDP  192.168.0.25:123        *:*
|   UDP  192.168.0.25:6771       *:*
|   UDP  192.168.0.25:55301      *:*
|_  UDP  224.0.0.251:5353     *:*
```

- snmp-sysdescr
```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-sysdescr 192.168.0.25Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:34 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.00045s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-sysdescr: Linux asus 4.9.4-galliumos-braswell #1 SMP PREEMPT galliumos2 Thu Feb 23 01:58:04 UTC 2017 x86_64
|_  System uptime: 2d21h33m34.15s (25041415 timeticks)Nmap done: 1 IP address (1 host up) scanned in 1.32 seconds
root@asus:~/unix%
```

- snmp-processes

```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-processes 192.168.0.25
Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:43 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.027s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-processes: 
|   1: 
|     Name: systemd
|     Path: /sbin/init
|     Params: splash
|   2: 
|     Name: kthreadd
|   3: 
|     Name: ksoftirqd/0
...Nmap done: 1 IP address (1 host up) scanned in 4.16 seconds
root@asus:~/unix%
```

snmp-w32-software


```
root@asus:~/unix% nmap -sU -p 161 --script=snmp-win32-software 192.168.0.25Starting Nmap 7.01 ( https://nmap.org ) at 2019-04-26 17:43 MDT
Nmap scan report for mgmt.acme.com (192.168.0.25)
Host is up (0.00049s latency).
PORT    STATE SERVICE
161/udp open  snmp
| snmp-win32-software: 
|   accountsservice-0.6.40-2ubuntu11.3; 0-01-01T00:00:00
|   acl-2.2.52-3; 0-01-01T00:00:00
|   adduser-3.113+nmu3ubuntu4; 0-01-01T00:00:00
|   adwaita-icon-theme-3.18.0-2ubuntu3.1; 0-01-01T00:00:00
|   alsa-base-1.0.25+dfsg-0ubuntu5; 0-01-01T00:00:00
|   alsa-utils-1.1.0-0ubuntu5; 0-01-01T00:00:00
|   anacron-2.3-23; 0-01-01T00:00:00
|   apache2-2.4.18-2ubuntu3.10; 0-01-01T00:00:00
|   apache2-bin-2.4.18-2ubuntu3.10; 0-01-01T00:00:00
|   apache2-data-2.4.18-2ubuntu3.10; 0-01-01T00:00:00
|   apache2-utils-2.4.18-2ubuntu3.10; 0-01-01T00:00:00
|   app-install-data-15.10; 0-01-01T00:00:00
|   apparmor-2.10.95-0ubuntu2.10; 0-01-01T00:00:00
|   apt-1.2.29ubuntu0.1; 0-01-01T00:00:00
|   apt-utils-1.2.29ubuntu0.1; 0-01-01T00:00:00
|   aptdaemon-1.1.1+bzr982-0ubuntu14; 0-01-01T00:00:00
|   aptdaemon-data-1.1.1+bzr982-0ubuntu14; 0-01-01T00:00:00
|   arc-theme-galliumos-0git20160407.46a232e-galliumos4; 0-01-01T00:00:00
|   aspell-0.60.7~20110707-3build1; 0-01-01T00:00:00
|   aspell-en-7.1-0-1.1; 0-01-01T00:00:00
|   at-spi2-core-2.18.3-4ubuntu1; 0-01-01T00:00:00
|   audacity-2.1.2-1; 0-01-01T00:00:00
|   audacity-data-2.1.2-1; 0-01-01T00:00:00
|   avahi-autoipd-0.6.32~rc+dfsg-1ubuntu2.3; 0-01-01T00:00:00
|   avahi-daemon-0.6.32~rc+dfsg-1ubuntu2.3; 0-01-01T00:00:00
|   avahi-utils-0.6.32~rc+dfsg-1ubuntu2.3; 0-01-01T00:00:00
...Nmap done: 1 IP address (1 host up) scanned in 26.03 seconds
root@asus:~/unix%
```