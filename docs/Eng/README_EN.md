# Навигация
1. [Что такое Сетезор?](#что-такое-сетезор)
2. [Особенности](#особенности-сетезор)
3. [Установка и запуск](установка-и-запуск) 
4. [Установка и запуск агента на сервере](#установка-и-запуск-агента-на-сервере)
5. [Поддержка](#поддержка)
6. [Донаты](#донаты)

![карта_сети](setezor/docs/4.png)

![графики](setezor/docs/5.png)

![уязвимости](setezor/docs/7.png)

![таблицы](setezor/docs/8.png)

# Что такое Сетезор?
 **Setezor** (formerly LMS.NetMap) is an analytical tool designed to monitor, analyze and optimize network operations. It collects and analyzes data from various sources on the network. Opens new horizons for information security, networking and system administration specialists.
 
Here are the key benefits that make it indispensable in the work:
- Web interface "HTTP REST API" on the server part.
- Tasks are performed only on agents, but there is no web interface and server control.
- Authorization and registration in the Software Setezor
- Invitation to Setisor or token project.
- Change of interface language: English or Russian.
- Division into projects.
- Visual display of data in tables and diagrams.
- Automatic construction of the network map at the L3-level.
- Formation of a group of goals (scopas and targets), allows you to create groups of IP addresses, ports and domains and groups scan information.
- Identification of IT assets and the inventory of IT infrastructure.
- Obtaining information in the form of tasks, when changing the status of the task, a notification surfaces.
- Scanning the network with tools SMAP, MSSPAN, SCAPY, SNMP.
- Web applications scan Domains, TLS/SSL CERT, WHOIS, WAPPALYZER.
- Scanning for vulnerability detection by ACUNETIX, CPEGiuss, SearchVuls.
- Identification of potentially dangerous exchange protocols (open and closed ports).
- Integration of various tools (logs loading, tool management)
- Loading xml-legs, pcap-legs, xml-legs, list-legs, json scanning logs.
- Search for software by network nodes and its version.
- Search for subdomains via DNS.
- Obtaining an SSL-certificate.
- Getting a list of vulnerabilities for a specific SearchVuls software tool.
- Search for a string by Brute-force SNMP community string.
 
# # Installation and launch
We divided the Setezor into two separate applications - the server and agents. The server part has a shell in the form of a web interface, it creates tasks. The agency part has no shell and contains only tools.

At the first start, Setezor fills the database and with it the password for the administrator "Admin password". It needs **to be preserved** and **remembered.**

## Server
####  DEB
Download deb-package from the repository [https://github.com/lmsecure/Setezor/releases]( https://github.com/lmsecure/Setezor/releases). When installing, make sure that you are located in the directory with a DEB packet, otherwise write a full path:

```bash
sudo apt install ./setezor_<версия>.deb
```

Declare the variables of the environment:

```bash
export SERVER_REST_URL=https://<ip/domain>:<port>
export SECRET_KEY=abcdef
```

Run the server:

```bash
setezor
```

#### Docker
Download server image from repository: [https://hub.docker.com/r/lmsecure/setezor](https://hub.docker.com/r/lmsecure/setezor)

```bash
docker pull lmsecure/setezor:latest
```

Create a working folder. It will be needed to store logs and user data:

```bash
mkdir ~/setezor && cd $_
```

Create a file ".env" and write in it variables:

```
SECRET_KEY=abcdef
SERVER_REST_URL=https://<ip/doamin>:<port>
```

Launch Server:
```bash
docker run -p 16661:16661 --env-file .env --network=host -v ~/setezor:/root/.local/share/setezor -d lmsecure/setezor:latest
```

## Agent
####  DEB
Download deb-package from repository  [https://github.com/lmsecure/Setezor.Agent/releases](https://github.com/lmsecure/Setezor.Agent/releases) and set by the team:

```bash
sudo apt install ./setezoragent_<версия>.deb
```

Launch of the agent:

```bash
setezoragent -p <порт>
```

#### Docker
Download the image of the agent from the repository: [https://hub.docker.com/r/lmsecure/setezor.agent/tags](https://hub.docker.com/r/lmsecure/setezor.agent/tags).

```bash
docker pull lmsecure/setezor.agent:latest
```

Launch of the agent:

```bash
docker run --network=host --cap-add=NET_ADMIN -d lmsecure/setezor.agent:latest
```

## Функционал CLI

- View all available options on the server:

```bash
setezor --help
```

- View all available options on the agent:

```bash
setezoragent --help
```

- Viewing users:

```bash
setezor list-users
```

-  Password reset:

```bash
setezor reset-password -l <username>
```


# Installing and running an agent on the server
The agent acts as the performer of tasks coming from the server, as well as in the role of an intermediary, sending data to the next agent, who may be the performer. It scans the network by interacting with the Setsor tools. It is able to connect not only through the server, but also through another agent. A connected agent can be tied to all projects.

Starting page **"Projects",** through the cap of the web page, go **"Admini Settings"** and **add** an agent.

![создать_агента](setezor/docs/1.png)

**Create a project** and link the agent to the project by going to **the** page **"Settings"** → **"Project"** → **"Connect** of agents".

In the table, the added agent **configure the interface** and save the changes.

More information can be found in the Setezor [документации](https://help.setezor.net).

# Support
If you have any difficulties or questions about using Setezor, we invite [https://t.me/netmap_chat](https://t.me/netmap_chat  ). our tg-chat. Also visit the Telegram channel [https://t.me/setezor](https://t.me/setezor) and the project site [https://setezor.ru](https://setezor.ru).

# Донаты
- Bitcoin: bc1qa2evk7khm246lhvljy8ujqu7m9m88gt84am9rz
- Dash: XoJ3pBDG6f5L6NwoqUqg7dpeT9MHKcNtwT

We accept any cryptocurrencies, write others.
