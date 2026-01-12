from enum import Enum


class MerchantPlan(str, Enum):
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"


class EmploymentType(str, Enum):
    SALARIED = "SALARIED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    BUSINESS = "BUSINESS"
    UNEMPLOYED = "UNEMPLOYED"


class InvoiceStatus(str, Enum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class WhatsAppDirection(str, Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class WhatsAppMessageType(str, Enum):
    INVOICE = "invoice"
    FOLLOWUP = "followup"
    CUSTOMER_MESSAGE = "customer_message"


class WhatsAppMessageStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    READ = "READ"
    FAILED = "FAILED"
    RECEIVED = "RECEIVED"


class RecurringInvoiceFrequency(str, Enum):
    MONTHLY = "MONTHLY"
