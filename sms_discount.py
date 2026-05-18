"""
SMS discount message template for Peakline Marketing outreach.
"""

SMS_DISCOUNT_TEMPLATE = (
    "Hey {business_name}! Peakline Marketing here — "
    "we help local detailers book 20-30 new leads/month with zero upfront risk. "
    "For a limited time, get 15% OFF your first month. "
    "Reply YES to grab your spot or call us to learn more. "
    "Reply STOP to opt out."
)


def build_sms(business_name: str) -> str:
    return SMS_DISCOUNT_TEMPLATE.format(business_name=business_name)


if __name__ == "__main__":
    print(build_sms("Mike's Auto Detail"))
