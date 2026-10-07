# How This Site Is Secured

## How do I know my data to this site is encrypted?

My website is available at `https://dueyy.me` and `https://www.dueyy.me`. HTTPS encrypts the connection between a visitor's browser and my web server so data sent across the Internet is protected while it is in transit.

The TLS certificate for my site was issued by Let's Encrypt. The certificate covers both `dueyy.me` and `www.dueyy.me` and expires on January 5, 2027.

I verified that both HTTPS addresses successfully load the site. I also tested the HTTP versions of both domains and confirmed that they return a `301` redirect to HTTPS.

## Certificate Renewal

Certbot manages the certificate and is configured to renew it automatically.

I tested certificate renewal with:

```bash
sudo certbot renew --dry-run
```

The test completed successfully:

```text
Congratulations, all simulated renewals succeeded:
/etc/letsencrypt/live/dueyy.me/fullchain.pem (success)
```

I also checked the Certbot renewal timer with:

```bash
systemctl list-timers | grep certbot
```

The timer showed that `certbot.timer` is scheduled to run automatically. At the time I checked it, the next scheduled run was:

```text
Wed 2026-10-07 23:36:29 UTC
certbot.timer
certbot.service
```

This means Certbot periodically checks the certificate and can automatically renew it when renewal is needed.

## Ports Open to the Internet

My Azure VM uses the following network ports:

- **Port 22 (SSH):** Used to administer the VM. The Azure `Allow-SSH-Laptop` rule restricts SSH access to my current public IP address using a `/32` source restriction.
- **Port 80 (HTTP):** Open to the Internet so HTTP requests can reach Nginx. Nginx redirects these requests to HTTPS.
- **Port 443 (HTTPS):** Open to the Internet for encrypted web traffic.
- **Port 8000:** Not open to the Internet. Uvicorn listens only on `127.0.0.1:8000`, so it can only be reached locally from inside the VM.

I tested port 8000 from outside the VM and the connection timed out, confirming that it is not publicly reachable.

## Where Encryption Starts and Ends

Encryption starts in the customer's browser when it connects to Nginx over HTTPS on port 443.

Nginx terminates the TLS connection on the Azure VM using the Let's Encrypt certificate. After Nginx decrypts the request, it forwards the request internally to the application at:

```text
http://127.0.0.1:8000
```

Uvicorn only listens on the VM's loopback interface, so this HTTP connection stays entirely inside the VM and is not exposed to the Internet.

Cloudflare is being used for DNS only. The DNS records for `dueyy.me` and `www.dueyy.me` point directly to the Azure VM rather than proxying web traffic through Cloudflare.

## How a Customer Can Check the Certificate

A customer can check the certificate in Chrome by:

1. Clicking the icon to the left of the domain.
2. Clicking **Connection is secure**.
3. Clicking **Certificate is valid**.

The certificate information shows the issuer, the domain names covered by the certificate, and the certificate's validity dates.

## OpenSSL Certificate Check

I checked the live certificate with:

```bash
echo | openssl s_client -connect dueyy.me:443 -servername dueyy.me 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

The actual output was:

```text
subject=CN = dueyy.me
issuer=C = US, O = Let's Encrypt, CN = YE1
notBefore=Oct  7 05:18:00 2026 GMT
notAfter=Jan  5 05:17:59 2027 GMT
```

I also checked Certbot's stored certificate information. It confirmed:

```text
Certificate Name: dueyy.me
Domains: dueyy.me www.dueyy.me
Expiry Date: 2027-01-05 05:17:59+00:00
```

These checks confirm that the certificate is valid for both domain names and that HTTPS encryption is active on the site.