# Custom tunneling server

If you wish to use your own server instead of localhost.run, you may follow these instructions.

We assume that you have server's ssh keys and the certbot is set up properly.

## Notes

Ssh remote port may fail to open due to an existing or ssh connection. I couldn't find the reason why the port is still being blocked, even if the old connection is closed.

See issue [#2](https://github.com/enaix/tg-remote-ssh/issues/2#issue-1206858295) for more details.

## Remote port

Please change the default port (`80`) in the ssh bot script to a different one (`1000-65535`), it must be different from the one in `listen` variable. We will use port `1234` in here.

## Nginx configuration (443 port is available)

If you don't have any other sites enabled in nginx, use this sample config (`/etc/nginx/sites-enabled/my-tunnel-config`).

Change `my-server.com` and `1234` to your server address and ssh tunnel port number (the first one in your ssh command).

```
server {
	listen 80;
	server_name my-server.com;
	return 301 https://$server_name$request_uri;
}

server {
	listen 443 ssl;
	server_name my-server.com;
	ssl_certificate /etc/letsencrypt/live/my-server.com/fullchain.pem;
	ssl_certificate_key /etc/letsencrypt/live/my-server.com/privkey.pem;
	
	location / {
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_read_timeout 90;
		proxy_pass http://127.0.0.1:1234;
	}

	location ~* /(api/kernels/[^/]+/(channels|iopub|shell|stdin)|terminals/websocket)/? {
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;

		proxy_http_version 1.1;
		proxy_set_header Upgrade "websocket";
		proxy_set_header Connection "Upgrade";
		proxy_read_timeout 86400;
		proxy_pass http://127.0.0.1:1234;
	}
}
```

## Nginx configuration (multiple enabled sites)

It's possible to enable ssl for multiple ports. If you wish to do so, please open your existing nginx configs and change all `server_name my-server.com;` to `server_name my-server.com default_server;` in `server` directives, where `listen 443 ssl;` exists. Otherwise, there would be a conflict.

```
server {
	# We don't change anything here
	...
	listen 80;
	...
	server_name my-server.com;
	...
}

server {
	# Add default_server here
	...
	listen 443 ssl;
	...
	server_name my-server.com default_server;
	...
}
```

Here's the sample config (`/etc/nginx/sites-enabled/my-tunnel-config`).

Change `8843` to your desirable port (the one that you will type in the url) and `my-server.com` to your server address.

`1234` is your ssh tunnel port number (the first one in your ssh command).

```
server {
	listen 8843 ssl;
	server_name my-server.com;
	ssl_certificate /etc/letsencrypt/live/my-server.com/fullchain.pem;
	ssl_certificate_key /etc/letsencrypt/live/my-server.com/privkey.pem;
	
	location / {
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_read_timeout 90;
		proxy_pass http://127.0.0.1:1234;
	}

	location ~* /(api/kernels/[^/]+/(channels|iopub|shell|stdin)|terminals/websocket)/? {
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;

		proxy_http_version 1.1;
		proxy_set_header Upgrade "websocket";
		proxy_set_header Connection "Upgrade";
		proxy_read_timeout 86400;
		proxy_pass http://127.0.0.1:1234;
	}
}
```

## Final configuration

Please restart nginx `sudo systemctl restart nginx` and don't forget to turn off password authentication.
