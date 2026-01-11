from enum import Enum


class MerchantPlan(str, Enum):
    TRIAL = "trial"
    STARTER = "starter"
    PRO = "pro"
