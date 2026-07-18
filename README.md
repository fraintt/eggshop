# 🥚 Egg Shop

A self-hosted web app for running a small egg-ordering business among friends or neighbors. Customers order eggs by the pack of 10 and get invoiced monthly with a Pay by Square QR code. Runs entirely on Docker Compose.

## Features

- Email-based customer signup with account verification
- Order eggs in packs of 10 at an admin-set price
- Order lifecycle: `pending → confirmed → completed → invoiced → paid`
- Monthly invoicing, automatic or on-demand, bundling each customer's delivered orders into one invoice
- Invoices as PDF with a scan-to-pay Pay by Square QR code
- Admin backend for orders, users, and shop settings (Django admin)
- Email notifications for new orders, cancellations, and invoices
- JSON API for Home Assistant (order counts, unpaid/paid totals)
- Multi-language UI: English, German, Slovak

## Quick start

```bash
git clone <this-repo>
cd eggshop
cp .env.example .env   # set DJANGO_SECRET_KEY and HA_API_TOKEN
docker compose up --build
```

- **http://localhost:8000** – the shop
- **http://localhost:8000/admin/** – admin backend
- **http://localhost:8025** – Mailhog (catches all outgoing email for local testing)

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

## Stack

Django · PostgreSQL · Celery + Redis · Docker Compose

## Docs

- [`README-full.md`](./README-full.md) – full setup, admin workflow, and configuration reference
- [`README-homeassistant.md`](./README-homeassistant.md) – Home Assistant integration guide

## Status

Built for hobby/internal use — no HTTPS, VAT invoicing, or backups configured out of the box. See `README-full.md` for what's intentionally out of scope.
