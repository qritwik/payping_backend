# PayPing API

**Stop chasing. Start getting paid.**

PayPing is a merchant management API that helps businesses manage invoices, customers, and recurring billing. Built with FastAPI, PostgreSQL, and Celery.

## Features

- 🔐 **OTP-based Authentication** - Secure phone number verification
- 👥 **Merchant Management** - Register and manage merchant accounts
- 📋 **Invoice Management** - Create, update, and manage invoices
- 🔄 **Recurring Invoices** - Automated recurring invoice generation
- 👤 **Customer Management** - Track and manage customer information
- 📱 **WhatsApp Integration** - Send invoice notifications via WhatsApp
- 🗄️ **PostgreSQL Database** - Robust data storage
- ⚡ **Celery Task Queue** - Asynchronous task processing
- 🐳 **Docker Support** - Easy deployment with Docker Compose

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Task Queue:** Celery with Redis
- **ORM:** SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens)
- **Storage:** Supabase S3
- **Monitoring:** Flower (Celery monitoring)

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker & Docker Compose (optional)

## Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd PayPing
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/payping
   SECRET_KEY=your-secret-key-change-in-production
   SUPABASE_ACCESS_KEY=your-supabase-access-key
   SUPABASE_SECRET_KEY=your-supabase-secret-key
   S3_ENDPOINT=your-s3-endpoint
   S3_REGION=your-s3-region
   ```

5. **Set up the database**
   ```bash
   # Run the schema SQL file
   psql -U postgres -d payping -f sql/payping_schema.sql
   ```

6. **Run the application**
   ```bash
   python run.py
   # Or
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **View logs**
   ```bash
   docker-compose logs -f api
   ```

3. **Stop services**
   ```bash
   docker-compose down
   ```

## Docker Services

- **api** - FastAPI application (port 8000)
- **celery-worker** - Celery worker for async tasks
- **flower** - Celery monitoring (port 5555)
- **redis** - Redis server (port 6379)
- **batch-generate-recurring-invoices** - Daily recurring invoice generation
- **batch-otp-cleanup-job** - Daily OTP cleanup

## Batch Jobs

### Recurring Invoice Generation

Generates invoices from recurring invoice templates. Run manually:
```bash
docker-compose run --rm batch-generate-recurring-invoices
```

Or schedule with cron:
```bash
0 2 * * * cd /path/to/PayPing && docker-compose run --rm batch-generate-recurring-invoices
```

### OTP Cleanup

Deletes expired OTPs from the database. Run manually:
```bash
docker-compose run --rm batch-otp-cleanup-job
```

Or schedule with cron:
```bash
0 3 * * * cd /path/to/PayPing && docker-compose run --rm batch-otp-cleanup-job
```

## API Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Authentication Endpoints

**Base Path:** `/api/v1/auth/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/send-otp` | Send OTP to phone number | No |
| `POST` | `/verify-otp` | Verify OTP and get access token (if merchant exists) | No |

**Note:** For detailed authentication flow, see [docs/AUTHENTICATION_FLOW.md](docs/AUTHENTICATION_FLOW.md)

### Merchant Endpoints

**Base Path:** `/api/v1/merchants/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/register` | Register a new merchant (requires OTP verification) | No |
| `GET` | `/me` | Get current merchant profile | Yes |
| `PUT` | `/me` | Update current merchant profile | Yes |
| `GET` | `/dashboard` | Get dashboard statistics (outstanding, paid this month, unpaid invoices, pending confirmations) | Yes |

### Customer Endpoints

**Base Path:** `/api/v1/customers/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/` | Create a new customer | Yes |
| `GET` | `/` | List all customers with total pending amount (unpaid invoices) | Yes |
| `GET` | `/{customer_id}` | Get customer details with total pending amount | Yes |
| `PUT` | `/{customer_id}` | Update customer details | Yes |
| `DELETE` | `/{customer_id}` | Delete a customer | Yes |
| `GET` | `/{customer_id}/invoices` | Get all invoices for a specific customer | Yes |

**Response Fields:**
- All customer endpoints include `total_pending_amount` - sum of all unpaid invoices for the customer

### Invoice Endpoints

**Base Path:** `/api/v1/invoices/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/` | Create a new invoice (sends WhatsApp notification if pause_reminder is false) | Yes |
| `GET` | `/` | List invoices with filters (status, customer_id, start_date, end_date) and pagination | Yes |
| `GET` | `/{invoice_id}` | Get invoice details (optionally include WhatsApp messages via `?include_messages=true`) | Yes |
| `PUT` | `/{invoice_id}` | Update invoice details (only if not PAID) | Yes |
| `DELETE` | `/{invoice_id}` | Soft delete an invoice (only if UNPAID) | Yes |
| `POST` | `/{invoice_id}/mark-paid` | Mark an invoice as paid | Yes |
| `POST` | `/{invoice_id}/send-followup` | Send a manual follow-up WhatsApp message for unpaid invoice | Yes |
| `POST` | `/{invoice_id}/pause-reminder` | Pause reminders for an invoice | Yes |
| `POST` | `/{invoice_id}/unpause-reminder` | Unpause reminders for an invoice | Yes |
| `GET` | `/{invoice_id}/whatsapp-messages` | Get all WhatsApp messages for a specific invoice | Yes |
| `GET` | `/public/{invoice_id}` | Get invoice and merchant details (public endpoint, no auth) | No |

**Query Parameters for GET `/`:**
- `status` - Filter by status (UNPAID, PAID)
- `customer_id` - Filter by customer UUID
- `start_date` - Filter invoices created from this date (YYYY-MM-DD)
- `end_date` - Filter invoices created until this date (YYYY-MM-DD)
- `skip` - Pagination offset (default: 0)
- `limit` - Pagination limit (default: 100, max: 1000)

### Recurring Invoice Endpoints

**Base Path:** `/api/v1/recurring-invoices/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/` | Create a new recurring invoice template | Yes |
| `GET` | `/` | List recurring invoice templates with filters (is_active, customer_id, start_date, end_date) and pagination | Yes |
| `GET` | `/{template_id}` | Get a specific recurring invoice template | Yes |
| `PUT` | `/{template_id}` | Update a recurring invoice template | Yes |
| `DELETE` | `/{template_id}` | Cancel/delete a recurring invoice template (sets is_active=false) | Yes |
| `POST` | `/{template_id}/pause` | Pause a recurring invoice template | Yes |
| `POST` | `/{template_id}/resume` | Resume a recurring invoice template | Yes |

**Query Parameters for GET `/`:**
- `is_active` - Filter by active status (true/false)
- `customer_id` - Filter by customer UUID
- `start_date` - Filter templates starting from this date
- `end_date` - Filter templates starting until this date
- `skip` - Pagination offset (default: 0)
- `limit` - Pagination limit (default: 100, max: 1000)

### Payment Confirmation Endpoints

**Base Path:** `/api/v1/payment-confirmations/`

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `GET` | `/` | List payment confirmations with filters (status) and pagination | Yes |
| `GET` | `/{confirmation_id}` | Get a specific payment confirmation by ID | Yes |
| `POST` | `/{confirmation_id}/approve` | Approve a payment confirmation and mark associated invoice as paid | Yes |
| `POST` | `/{confirmation_id}/decline` | Decline a payment confirmation | Yes |

**Query Parameters for GET `/`:**
- `status` - Filter by status (pending, approved, rejected)
- `skip` - Pagination offset (default: 0)
- `limit` - Pagination limit (default: 100, max: 1000)

### Authentication

Most endpoints require authentication via JWT Bearer token. Include the token in the Authorization header:

```
Authorization: Bearer <your-access-token>
```

Tokens are obtained through the `/api/v1/auth/verify-otp` endpoint after OTP verification.

## Configuration

Key configuration options in `app/core/config.py`:

- `OTP_EXPIRY_MINUTES` - OTP expiration time (default: 10 minutes)
- `OTP_LENGTH` - OTP code length (default: 6)
- `OTP_RATE_LIMIT_SECONDS` - Minimum seconds between OTP requests (default: 60)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - JWT token expiration (default: 30 minutes)

## Project Structure

```
PayPing/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core configuration and database
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic services
│   ├── tasks/           # Celery tasks
│   └── utils/           # Utility functions
├── batch_jobs/          # Scheduled batch jobs
├── docs/               # Documentation
├── sql/                # Database schema files
├── test/               # Test files
├── docker-compose.yml  # Docker services configuration
├── Dockerfile          # Docker image definition
└── requirements.txt    # Python dependencies
```

## Development

### Running Tests

```bash
# Add test commands here when tests are set up
```

### Code Style

Follow PEP 8 guidelines for Python code.

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.
