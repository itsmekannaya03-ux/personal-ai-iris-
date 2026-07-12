from ..core.config import settings

# Placeholder for Stripe integration
# In production, use:
#   import stripe
#   stripe.api_key = settings.STRIPE_SECRET_KEY

PLANS = {
    "student": {
        "price_id": "price_student_monthly",  # Replace with actual Stripe price ID
        "amount": 9900,  # ₹99 in paise
        "currency": "INR",
    },
    "lifetime": {
        "price_id": "price_lifetime",
        "amount": 99900,  # ₹999 in paise
        "currency": "INR",
    },
}


def create_checkout_session(user_id: str, plan: str, base_url: str) -> str:
    """Create a Stripe Checkout Session and return the URL."""
    # In production:
    #   session = stripe.checkout.Session.create(
    #       line_items=[{"price": PLANS[plan]["price_id"], "quantity": 1}],
    #       mode="subscription" if plan == "student" else "payment",
    #       client_reference_id=user_id,
    #       success_url=f"{base_url}/auth/callback?session_id={{CHECKOUT_SESSION_ID}}",
    #       cancel_url=f"{base_url}/pricing",
    #   )
    #   return session.url
    return f"{base_url}/dashboard/download"
