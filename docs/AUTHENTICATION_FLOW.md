# Authentication Flow Documentation

## Overview
PayPing uses OTP-based authentication via phone numbers. Both registration and login follow a simple two-step OTP verification process.

---

## 🔐 Registration Flow

### Step 1: Send OTP
**Endpoint:** `POST /api/v1/auth/send-otp`

**Request:**
```json
{
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "phone": "+1234567890"
}
```

---

### Step 2: Verify OTP
**Endpoint:** `POST /api/v1/auth/verify-otp`

**Request:**
```json
{
  "phone": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "message": "OTP verified successfully. Please complete registration.",
  "verified": true,
  "access_token": null,
  "token_type": null,
  "requires_registration": true
}
```

---

### Step 3: Register Merchant
**Endpoint:** `POST /api/v1/merchants/register`

**Request:**
```json
{
  "business_name": "My Business",
  "business_type": "Retail",
  "business_address": "123 Main St",
  "business_city": "New York",
  "business_country": "USA",
  "business_zipcode": "10001",
  "owner_name": "John Doe",
  "phone": "+1234567890",
  "email": "john@example.com",
  "company_logo_s3_url": "https://...",
  "upi_id": "merchant@upi",
  "upi_qr_s3_url": "https://..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "merchant": {
    "id": "uuid-here",
    "business_name": "My Business",
    "phone": "+1234567890",
    "status": "active",
    "created_at": "2024-01-01T00:00:00",
    ...
  }
}
```

**Note:** You receive a JWT token immediately after registration. No need to verify OTP again!

---

## 🔑 Login Flow

### Step 1: Send OTP
**Endpoint:** `POST /api/v1/auth/send-otp`

**Request:**
```json
{
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "phone": "+1234567890"
}
```

---

### Step 2: Verify OTP & Get Token
**Endpoint:** `POST /api/v1/auth/verify-otp`

**Request:**
```json
{
  "phone": "+1234567890",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "message": "OTP verified successfully",
  "verified": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "requires_registration": false
}
```

**Note:** If the merchant exists, you get a JWT token immediately. If not, you'll get `requires_registration: true` and need to complete registration.

---

## 📋 Quick Reference

### Registration (3 steps)
1. `POST /api/v1/auth/send-otp` → Get OTP
2. `POST /api/v1/auth/verify-otp` → Verify OTP
3. `POST /api/v1/merchants/register` → Create account + Get token

### Login (2 steps)
1. `POST /api/v1/auth/send-otp` → Get OTP
2. `POST /api/v1/auth/verify-otp` → Verify OTP + Get token

---

## 🔒 Using Authenticated Endpoints

After receiving the JWT token, include it in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

### Protected Endpoints
- `GET /api/v1/merchants/me` - Get current merchant profile

---

## ⚠️ Important Notes

1. **OTP Expiry:** OTPs expire after a configured time (check settings)
2. **OTP Verification Required:** Registration requires verified OTP - cannot skip this step
3. **Phone Number:** Must match between OTP verification and registration
4. **Duplicate Prevention:** Cannot register with an existing phone number
5. **Auto-Authentication:** JWT token is automatically returned after successful registration

---

## 🚨 Error Responses

### Invalid OTP
```json
{
  "detail": "Invalid or expired OTP"
}
```

### OTP Not Verified (Registration)
```json
{
  "detail": "OTP verification required. Please verify your phone number first."
}
```

### Merchant Already Exists
```json
{
  "detail": "Merchant with this phone number already exists"
}
```

---

## 📝 Example Flow

### Registration Example
```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'

# Step 2: Verify OTP
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "otp_code": "123456"}'

# Step 3: Register
curl -X POST http://localhost:8000/api/v1/merchants/register \
  -H "Content-Type: application/json" \
  -d '{
    "business_name": "My Business",
    "phone": "+1234567890",
    "email": "john@example.com"
  }'
```

### Login Example
```bash
# Step 1: Send OTP
curl -X POST http://localhost:8000/api/v1/auth/send-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890"}'

# Step 2: Verify OTP & Get Token
curl -X POST http://localhost:8000/api/v1/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"phone": "+1234567890", "otp_code": "123456"}'
```

