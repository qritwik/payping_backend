-- =========================================
-- PayPing – Final PostgreSQL Schema
-- Stop chasing. Start getting paid.
-- =========================================


-- ---------- EXTENSIONS ----------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---------- OTP Table ----------
CREATE TABLE IF NOT EXISTS otps (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  phone VARCHAR(15) NOT NULL,
  otp_code VARCHAR(6) NOT NULL,
  is_verified VARCHAR(10) DEFAULT 'false',
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_otps_phone ON otps(phone);

-- ---------- MERCHANTS ----------
CREATE TABLE IF NOT EXISTS merchants (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  business_name        VARCHAR(150) NOT NULL,
  business_type        VARCHAR(100),
  business_address     TEXT,
  business_city        VARCHAR(50),
  business_country     VARCHAR(50),
  business_zipcode     VARCHAR(20),

  owner_name           VARCHAR(100),
  phone                VARCHAR(15) UNIQUE NOT NULL,
  email                VARCHAR(150),

  company_logo_s3_url  TEXT,
  upi_id               VARCHAR(100),
  upi_qr_s3_url        TEXT,

  is_active            BOOLEAN DEFAULT TRUE NOT NULL,
  plan                 VARCHAR(20) DEFAULT 'trial' NOT NULL CHECK (plan IN ('trial', 'starter', 'pro')),
  created_at           TIMESTAMP DEFAULT NOW()
);

-- ---------- SUBSCRIPTIONS ----------
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,

  plan VARCHAR(20) NOT NULL CHECK (plan IN ('STARTER', 'PRO')),
  invoice_limit INT NOT NULL,

  billing_start DATE NOT NULL,
  billing_end DATE NOT NULL,

  status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE', 'EXPIRED')),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Only ONE ACTIVE subscription per merchant
CREATE UNIQUE INDEX IF NOT EXISTS uniq_active_subscription
ON subscriptions (merchant_id)
WHERE status = 'ACTIVE';

-- ---------- CUSTOMERS ----------
CREATE TABLE IF NOT EXISTS customers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,

  name VARCHAR(100) NOT NULL,
  phone VARCHAR(15) NOT NULL,

  email VARCHAR(150),
  address TEXT,
  employment_type VARCHAR(20) CHECK (employment_type IN ('SALARIED', 'SELF_EMPLOYED', 'BUSINESS', 'UNEMPLOYED')),
  class VARCHAR(100),
  section VARCHAR(100),
  batch VARCHAR(100),

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customers_merchant_id ON customers(merchant_id);

-- ---------- INVOICES ----------
CREATE TABLE IF NOT EXISTS invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,

  invoice_number VARCHAR(50),
  description TEXT,

  amount DECIMAL(10,2) NOT NULL,
  due_date DATE,

  status VARCHAR(20) DEFAULT 'UNPAID'
    CHECK (status IN ('UNPAID', 'PAID')),

  paid_at TIMESTAMP,
  pause_reminder BOOLEAN DEFAULT FALSE,
  deleted_at TIMESTAMP,

  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_merchant_id ON invoices(merchant_id);
CREATE INDEX IF NOT EXISTS idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);

-- ---------- WHATSAPP MESSAGES ----------
CREATE TABLE IF NOT EXISTS whatsapp_messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  invoice_id UUID REFERENCES invoices(id) ON DELETE SET NULL,

  direction TEXT NOT NULL
    CHECK (direction IN ('INBOUND', 'OUTBOUND')),

  message_type TEXT
    CHECK (message_type IN ('invoice', 'followup', 'customer_message')),

  status TEXT NOT NULL DEFAULT 'PENDING'
    CHECK (status IN (
      'PENDING',
      'SENT',
      'DELIVERED',
      'READ',
      'FAILED',
      'RECEIVED'
    )),

  message_text TEXT,
  provider_message_id TEXT UNIQUE,

  detected_intent TEXT,
  llm_confidence NUMERIC(3,2),

  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_merchant_id ON whatsapp_messages(merchant_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_customer_id ON whatsapp_messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_invoice_id ON whatsapp_messages(invoice_id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_messages_provider_id ON whatsapp_messages(provider_message_id);

-- ---------- PAYMENT CONFIRMATIONS ----------
CREATE TABLE IF NOT EXISTS payment_confirmations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  invoice_id UUID REFERENCES invoices(id) ON DELETE CASCADE,
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  whatsapp_message_id UUID REFERENCES whatsapp_messages(id) ON DELETE SET NULL,

  customer_message TEXT,
  detected_intent TEXT,
  llm_confidence NUMERIC(3,2),

  status TEXT CHECK (status IN ('pending', 'approved', 'rejected')),

  created_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payment_confirmations_invoice_id ON payment_confirmations(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_confirmations_merchant_id ON payment_confirmations(merchant_id);
CREATE INDEX IF NOT EXISTS idx_payment_confirmations_status ON payment_confirmations(status);

-- ---------- RECURRING INVOICES ----------
CREATE TABLE IF NOT EXISTS recurring_invoices (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  merchant_id UUID REFERENCES merchants(id) ON DELETE CASCADE NOT NULL,
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE NOT NULL,

  invoice_number_prefix VARCHAR(50),
  description TEXT,

  amount DECIMAL(10,2) NOT NULL,
  day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 31),
  due_date_offset INTEGER NOT NULL DEFAULT 7,
  pause_reminder BOOLEAN DEFAULT FALSE NOT NULL,
  
  start_date DATE NOT NULL,
  end_date DATE,
  next_generation_date DATE NOT NULL,
  
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  frequency VARCHAR(20) DEFAULT 'MONTHLY' NOT NULL CHECK (frequency IN ('MONTHLY')),
  
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_recurring_invoices_merchant_id ON recurring_invoices(merchant_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_customer_id ON recurring_invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_is_active ON recurring_invoices(is_active);
CREATE INDEX IF NOT EXISTS idx_recurring_invoices_next_generation_date ON recurring_invoices(next_generation_date);

-- Add recurring_invoice_id to invoices table (after recurring_invoices table is created)
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS recurring_invoice_id UUID REFERENCES recurring_invoices(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_invoices_recurring_invoice_id ON invoices(recurring_invoice_id);
