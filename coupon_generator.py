
import random
import string

def generate_coupon_code(length=6):
    """Generate a random coupon code of given length."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def generate_multiple_coupon_codes(num_coupons, length=6):
    """Generate multiple coupon codes."""
    return [generate_coupon_code(length) for _ in range(num_coupons)]
