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
