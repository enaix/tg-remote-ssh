# Telegram remote access bot

### Freely access your PC over ssh

## Features:
* Ngrok ssh service
* Webserver with encrypted tls (localhost.run)
* Jupyter notebook support (token extraction)

## Installation

Run `pip3 install -r requirements.txt`

## Linux

Execute `./install.sh` to install Systemd services (tgbot, jupyter, lo-ssh and ngrok-ssh)

In order to add each service to autostart, run `sudo systemctl enable <service>`

To start/stop/restart services, run `sudo systemctl <action> <service>`

## Not Linux

Unfortunately, other OS are not supported

## Configuration

### Common

Edit the `settings` file

Some of the configuration options:
* `enable_*`: Enable each service
* `notify_on_login`: Message admins when someone tries to login
* `spam_threshold`: Spam users threshold
* `glue_webtoken`: Post the whole link with the webtoken (Jupyter only)

### Web server

Edit the `tools/lo-ssh/start-lo` file and change the 8888 port to your desired local port. Don't forget to execute the `start-lo` script manually in order to add localhost.run to known_hosts.

### Ngrok

*Never start ngrok without configuring sshd, bad configuration may lead to a hack!*
Disable password authentication in /etc/ssh/sshd.config.
Make sure that `ngrok` binary is in `$PATH` and edit the command in `tools/ngrok-ssh/start-ngrok`
