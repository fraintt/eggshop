# 🥚 Egg Shop

A small Django web app for running an egg-ordering side business among
friends: customers sign up, order eggs by the pack of 10, and get invoiced
monthly with a Pay by Square QR code. Runs entirely via Docker Compose.

## What's included

- Email-based customer registration (signup + email confirmation link)
- Customer ordering: packs of 10 eggs, at the current admin-set price
- Order lifecycle: `pending → confirmed → completed → invoiced → paid`
  (+ `cancelled`, by customer or admin, while pending/confirmed)
- Admin backend (Django admin): order overview & status actions, user
  management, shop settings (price, IBAN)
- Monthly invoicing: bundles every customer's `completed`, not-yet-invoiced
  orders into one invoice, either automatically (1st of the month) or
  on-demand via a "Run invoicing now" button in the admin
- Invoices as PDF with an embedded Pay by Square QR code (scan-to-pay,
  no manual bank details entry), plus a customer-facing invoice history page
- Admin manually marks invoices as paid (Pay by Square doesn't confirm
  payment automatically)
- Email notifications: admin gets pinged on new orders, customers get
  notified on cancellations and when a new invoice is ready
- A simple token-authenticated JSON endpoint for Home Assistant
  (`/api/ha/summary/`) - see `README-homeassistant.md`
- A little egg-carton themed UI
- Multi-language UI (English, German, Slovak) with a language switcher; each
  customer's chosen language is also remembered for the emails they get
  (order confirmations, invoices, etc.) even though those are sent from a
  background worker, not a live page request

## Quick start

```bash
cp .env.example .env
# edit .env: set DJANGO_SECRET_KEY and HA_API_TOKEN to random strings
docker compose up --build
```

Then visit:
- **http://localhost:8000** - the shop (sign up, place an order)
- **http://localhost:8000/admin/** - Django admin
- **http://localhost:8025** - Mailhog, catches every email sent by the app
  so you can test signup/order/invoice emails without a real mail server

Create an admin user:

```bash
docker compose exec web python manage.py createsuperuser
```

Then log into `/admin/` and, under **Shop settings**, set your egg price
and IBAN (required for the Pay by Square QR code on invoices).

## Day-to-day admin workflow

1. A customer signs up (receives a confirmation email - check Mailhog while
   testing) and places an order.
2. You get an email notification. In `/admin/shop/order/`, select the order
   and run **"Mark selected orders as confirmed"**.
3. Once eggs are delivered, select it again and run
   **"Mark selected orders as completed (delivered)"**.
4. If something can't be fulfilled, use **"Cancel selected orders"**
   instead (only works while pending/confirmed) - the customer is emailed
   automatically.
5. At the end of the month (or any time you like, via the **"Run invoicing
   now"** button on `/admin/invoicing/invoice/`), every customer with
   completed-but-unbilled orders gets a new invoice, emailed to them as a
   PDF with a QR code. Orders with nothing to bill are skipped - no empty
   invoices.
6. When a bank transfer comes in, open the invoice in admin and run
   **"Mark selected invoices as paid"** - the customer gets a confirmation
   email. Unpaid invoices stay open indefinitely; they are never merged
   into the next invoice run.

Customers can see their own order and invoice history any time by logging in.

## Configuration reference (`.env`)

| Variable | Purpose |
|---|---|
| `DJANGO_SECRET_KEY` | Django's cryptographic secret - set to something random |
| `DJANGO_DEBUG` | `True` while testing, `False` once this is exposed beyond your LAN |
| `DJANGO_ALLOWED_HOSTS` / `DJANGO_CSRF_TRUSTED_ORIGINS` | hostnames the app will answer for |
| `POSTGRES_*` | database credentials |
| `EMAIL_*` | SMTP settings - defaults to the bundled Mailhog for testing |
| `ADMIN_NOTIFICATION_EMAIL` | who gets "new order" emails; leave blank to notify every staff user |
| `HA_API_TOKEN` | required for the Home Assistant endpoint to respond at all |

## Notes on scope / what's intentionally simple

This was built for a small hobby operation among friends, so a few things
were deliberately kept out to match that:

- **No HTTPS/reverse proxy** - it's plain HTTP on port 8000, meant for
  internal/LAN testing. Put Traefik/Nginx/Caddy in front when you're ready
  to expose it beyond your network, and set `DJANGO_DEBUG=False` at that point.
- **No VAT/legal invoice numbering** - invoices get a simple sequential
  `eggpayNNNN` number, not a legally compliant business invoice sequence.
- **No stock limits** - customers can order any number of packs; admin
  cancels orders manually if there isn't enough stock.
- **No automatic payment matching** - the QR code makes paying easy for the
  customer, but you still confirm receipt and mark the invoice paid by hand.
- **No backups configured** - the Postgres volume is durable across
  restarts, but nothing ships it off-box. Worth adding if this grows beyond
  "hobby" status.
- **Migrations are generated at container startup** (`makemigrations` runs
  automatically before `migrate`) rather than being committed to the repo -
  simplest thing that works for a single-environment hobby deploy. If you
  later want a "real" migration history (e.g. multiple environments), run
  `docker compose exec web python manage.py makemigrations` once, commit the
  generated files under `shop/migrations/` and `invoicing/migrations/`, and
  drop the `makemigrations` step from `docker-compose.yml`.

## Extending it later

- Order/invoice status-change emails (e.g. "your order was confirmed") -
  the email helpers in `shop/emails.py` and `invoicing/emails.py` are
  already there to extend.
- Bank statement (CAMT.053) import to auto-match payments instead of
  marking invoices paid by hand.
- Multiple products/egg types - currently there's a single product
  ("pack of 10 eggs") with one admin-editable price.
- The invoice PDF itself (`invoicing/pdf.py`) is still English-only -
  translating it would mean swapping its hardcoded strings for `gettext`
  calls, same pattern as everywhere else.

## Languages

The UI ships in English, German, and Slovak. The switcher in the top nav
sets a cookie for browsing and, for logged-in customers, also saves the
choice to their profile - that's what background jobs (order/invoice
emails sent by Celery, not from a live page request) use to pick the right
language, since there's no browser cookie to read at that point.

Translated text lives in `locale/de/LC_MESSAGES/django.po` and
`locale/sk/LC_MESSAGES/django.po` - plain text files, one `msgid`/`msgstr`
pair per string. To fix wording or add missing translations, edit those
directly (no special tooling needed, they're just text). The Docker image
compiles them automatically at build time, so `docker compose up --build`
picks up any edits.

To add a new customer-facing string in a template, wrap it in Django's
translation tags, e.g. `{% trans "New text" %}` (add `{% load i18n %}` at
the top of the template if it's not already there), then add a matching
`msgid "New text"` / `msgstr "..."` pair to both `.po` files. To add a
whole new language, copy `locale/de` to `locale/<code>/`, translate the
`msgstr` values, and add `("<code>", "<Native name>")` to `LANGUAGES` in
`eggshop/settings.py`.
