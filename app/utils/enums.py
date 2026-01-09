from enum import Enum


class MerchantStatus(str, Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
