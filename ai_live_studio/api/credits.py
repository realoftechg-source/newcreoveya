"""
Credits module. Handles the business logic around consuming and
awarding credits. The actual streaming-cost calculation is left as a
placeholder so you can tune pricing to match your real AI API's costs.
"""

CREDITS_PER_MINUTE = {
    'low': 1,
    'medium': 2,
    'high': 4,
    'ultra': 8,
}


def calculate_stream_cost(quality, minutes):
    """
    Placeholder cost model. Replace with real pricing once your AI
    provider's per-minute cost is known.

    # INSERT MY API HERE (e.g. pull live pricing from a provider)
    """
    rate = CREDITS_PER_MINUTE.get(quality, 2)
    return int(rate * minutes)


def charge_user(user, amount, description=''):
    """Deduct credits from a user's balance. Returns True on success."""
    return user.deduct_credits(amount)


def refund_user(user, amount, description=''):
    """Refund credits to a user's balance."""
    user.add_credits(amount)
    return True
