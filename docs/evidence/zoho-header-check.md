# Zoho Email Header Check

## 1. Message authentication result

The saved Outlook message-details screenshot shows:

- SPF: pass
- DKIM: pass (`header.d=dueyy.me`)
- DMARC: pass (`header.from=dueyy.me`)
- ARC: pass
- Sender/header domain shown: `dueyy.me`

## 2. What each result means

- MX records control where inbound mail for a domain is delivered.
- SPF identifies sending systems authorized for a domain.
- DKIM verifies the message's domain-associated cryptographic signature.
- DMARC evaluates whether SPF and/or DKIM align with the visible From domain
  and applies the domain's published policy.

## 3. Evidence

![Outlook message authentication details](./ex06-email-auth.png)

## 4. Delivery checks recorded in Exercise 06

[`ex06.md`](ex06.md) records that an external test message was received at the
`dueyy.me` mailbox, a reply from that mailbox arrived in Outlook, and a new
outbound message from `dueyy.me` arrived in Outlook.

## 5. Before-MX check

Before-MX delivery result: not contemporaneously recorded; unverified.
