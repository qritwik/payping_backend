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

### Main Endpoints

- **Authentication:** `/api/v1/auth/`
  - `POST /send-otp` - Send OTP to phone number
  - `POST /verify-otp` - Verify OTP and get access token

- **Merchants:** `/api/v1/merchants/`
  - `POST /register` - Register a new merchant
  - `GET /me` - Get current merchant profile (authenticated)

- **Customers:** `/api/v1/customers/`
  - `POST /` - Create a customer
  - `GET /` - List customers
  - `GET /{id}` - Get customer details

- **Invoices:** `/api/v1/invoices/`
  - `POST /` - Create an invoice
  - `GET /` - List invoices
  - `GET /{id}` - Get invoice details
  - `PUT /{id}` - Update invoice

- **Recurring Invoices:** `/api/v1/recurring-invoices/`
  - `POST /` - Create recurring invoice template
  - `GET /` - List recurring invoices
  - `GET /{id}` - Get recurring invoice details

For detailed authentication flow, see [docs/AUTHENTICATION_FLOW.md](docs/AUTHENTICATION_FLOW.md)

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
