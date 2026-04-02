# ============================================
# PAYMENTS.PY - COMPLETE PAYMENT PROCESSING
# KINVA MASTER PRO - UPI, STARS, PAYPAL, CRYPTO
# ============================================

import os
import logging
import json
import uuid
import qrcode
import hashlib
import hmac
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any
from io import BytesIO
from decimal import Decimal

from config import Config
from database import db
from premium import PremiumPlan, premium_manager

logger = logging.getLogger(__name__)


class PaymentManager:
    """Complete Payment Processing System"""
    
    def __init__(self):
        self.pending_payments = {}
        self.upi_id = Config.UPI_ID
        self.upi_name = Config.UPI_NAME
        
    # ============================================
    # UPI PAYMENT METHODS
    # ============================================
    
    def generate_upi_qr(self, amount: float, user_id: int, plan: str) -> Tuple[str, str]:
        """Generate UPI QR code for payment"""
        transaction_id = self.generate_transaction_id(user_id)
        
        # Create UPI payment URL
        upi_url = f"upi://pay?pa={self.upi_id}&pn={self.upi_name}&am={amount}&cu=INR&tn=Premium_{plan}_{transaction_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_path = os.path.join(Config.TEMP_DIR, f"upi_qr_{transaction_id}.png")
        qr_image.save(qr_path)
        
        # Store pending payment
        self.pending_payments[transaction_id] = {
            'user_id': user_id,
            'amount': amount,
            'plan': plan,
            'method': 'upi',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        return qr_path, transaction_id
    
    def get_upi_payment_text(self, amount: float, transaction_id: str) -> str:
        """Get UPI payment instruction text"""
        return f"""
💳 **UPI PAYMENT DETAILS**

━━━━━━━━━━━━━━━━━━━━━━
**UPI ID:** `{self.upi_id}`
**Name:** {self.upi_name}
**Amount:** ₹{amount}

**Transaction ID:** `{transaction_id}`

━━━━━━━━━━━━━━━━━━━━━━
**📱 Steps to Pay:**

1️⃣ Open any UPI app (Google Pay, PhonePe, Paytm)
2️⃣ Scan the QR code below
3️⃣ Pay ₹{amount} to {self.upi_name}
4️⃣ Send confirmation: `/confirm {transaction_id}`

━━━━━━━━━━━━━━━━━━━━━━
⚠️ **Important:**
• Premium activates within 24 hours
• Keep transaction ID for reference
• Contact @support for issues
        """
    
    # ============================================
    # TELEGRAM STARS PAYMENT
    # ============================================
    
    def create_stars_invoice(self, user_id: int, plan: str) -> Dict:
        """Create Telegram Stars invoice"""
        transaction_id = self.generate_transaction_id(user_id)
        
        # Get star price based on plan
        star_prices = {
            'monthly': Config.PREMIUM_PRICE_MONTHLY_STARS,
            'yearly': Config.PREMIUM_PRICE_YEARLY_STARS,
            'lifetime': Config.PREMIUM_PRICE_LIFETIME_STARS
        }
        
        star_amount = star_prices.get(plan, Config.PREMIUM_PRICE_MONTHLY_STARS)
        
        # Store pending payment
        self.pending_payments[transaction_id] = {
            'user_id': user_id,
            'amount': star_amount,
            'plan': plan,
            'method': 'stars',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        return {
            'transaction_id': transaction_id,
            'star_amount': star_amount,
            'title': f"Kinva Master Pro - {plan.upper()} Premium",
            'description': f"Unlock all premium features for {plan}\n\nBenefits:\n• 4GB File Support\n• 60 Min Videos\n• No Watermark\n• 4K Export\n• 100+ Filters\n• Priority Processing",
            'payload': transaction_id,
            'currency': 'XTR',  # Telegram Stars
            'prices': [{'label': f"{plan.upper()} Premium", 'amount': star_amount}]
        }
    
    # ============================================
    # PAYPAL PAYMENT
    # ============================================
    
    def create_paypal_payment(self, user_id: int, plan: str, return_url: str, cancel_url: str) -> Optional[Dict]:
        """Create PayPal payment"""
        # Get price based on plan
        prices = {
            'monthly': Config.PREMIUM_PRICE_MONTHLY_USD,
            'yearly': Config.PREMIUM_PRICE_YEARLY_USD,
            'lifetime': Config.PREMIUM_PRICE_LIFETIME_USD
        }
        
        amount = prices.get(plan, Config.PREMIUM_PRICE_MONTHLY_USD)
        transaction_id = self.generate_transaction_id(user_id)
        
        # Store pending payment
        self.pending_payments[transaction_id] = {
            'user_id': user_id,
            'amount': amount,
            'plan': plan,
            'method': 'paypal',
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        # In production, integrate with PayPal API
        paypal_link = f"https://www.paypal.com/paypalme/kinvamaster/{amount}"
        
        return {
            'transaction_id': transaction_id,
            'amount': amount,
            'paypal_link': paypal_link,
            'instructions': f"Send ${amount} to @kinvamaster on PayPal with transaction ID: {transaction_id}"
        }
    
    # ============================================
    # CRYPTO PAYMENT (USDT/BTC)
    # ============================================
    
    def get_crypto_address(self, currency: str = "USDT") -> Dict:
        """Get crypto wallet address"""
        addresses = {
            'USDT': Config.CRYPTO_WALLET_USDT or "TXjVgYzLZjLZzXzXzXzXzXzXzXzXzXz",
            'BTC': Config.CRYPTO_WALLET_BTC or "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        }
        
        return {
            'currency': currency,
            'address': addresses.get(currency, addresses['USDT']),
            'network': 'TRC20' if currency == 'USDT' else 'BTC'
        }
    
    def create_crypto_payment(self, user_id: int, plan: str, currency: str = "USDT") -> Dict:
        """Create crypto payment request"""
        # Get price in USD
        prices = {
            'monthly': Config.PREMIUM_PRICE_MONTHLY_USD,
            'yearly': Config.PREMIUM_PRICE_YEARLY_USD,
            'lifetime': Config.PREMIUM_PRICE_LIFETIME_USD
        }
        
        amount_usd = prices.get(plan, Config.PREMIUM_PRICE_MONTHLY_USD)
        transaction_id = self.generate_transaction_id(user_id)
        
        # Store pending payment
        self.pending_payments[transaction_id] = {
            'user_id': user_id,
            'amount': amount_usd,
            'plan': plan,
            'method': 'crypto',
            'currency': currency,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        
        crypto_address = self.get_crypto_address(currency)
        
        return {
            'transaction_id': transaction_id,
            'amount_usd': amount_usd,
            'currency': currency,
            'address': crypto_address['address'],
            'network': crypto_address['network'],
            'instructions': f"Send {amount_usd} USD worth of {currency} to the address above"
        }
    
    # ============================================
    # PAYMENT VERIFICATION
    # ============================================
    
    def generate_transaction_id(self, user_id: int) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        return f"KINVA_{timestamp}_{user_id}_{unique_id}"
    
    def verify_upi_payment(self, transaction_id: str, user_id: int) -> Tuple[bool, str]:
        """Verify UPI payment (manual verification)"""
        if transaction_id not in self.pending_payments:
            return False, "Transaction not found"
        
        payment = self.pending_payments[transaction_id]
        
        if payment['user_id'] != user_id:
            return False, "Transaction doesn't belong to you"
        
        if payment['status'] == 'completed':
            return False, "Transaction already completed"
        
        # Mark as pending admin verification
        payment['status'] = 'pending_verification'
        
        return True, "Payment recorded. Admin will verify and activate premium within 24 hours."
    
    def verify_stars_payment(self, payload: str) -> Tuple[bool, str]:
        """Verify Telegram Stars payment"""
        if payload not in self.pending_payments:
            return False, "Transaction not found"
        
        payment = self.pending_payments[payload]
        
        if payment['status'] == 'completed':
            return False, "Transaction already completed"
        
        # Mark as completed
        payment['status'] = 'completed'
        
        # Activate premium
        plan_map = {
            'monthly': PremiumPlan.MONTHLY,
            'yearly': PremiumPlan.YEARLY,
            'lifetime': PremiumPlan.LIFETIME
        }
        
        plan = plan_map.get(payment['plan'], PremiumPlan.MONTHLY)
        
        # Record transaction in database
        transaction_id = self.generate_transaction_id(payment['user_id'])
        db.add_transaction(
            user_id=payment['user_id'],
            amount=payment['amount'],
            payment_method='stars',
            transaction_id=transaction_id,
            stars_amount=payment['amount'],
            plan_type=payment['plan'],
            duration_days=plan.value['days'] if hasattr(plan, 'value') else 30
        )
        
        # Activate premium
        premium_manager.activate_premium(
            payment['user_id'], 
            plan, 
            'stars', 
            transaction_id
        )
        
        return True, "Payment verified! Premium activated successfully!"
    
    def verify_crypto_payment(self, transaction_id: str, tx_hash: str) -> Tuple[bool, str]:
        """Verify crypto payment (simplified)"""
        if transaction_id not in self.pending_payments:
            return False, "Transaction not found"
        
        payment = self.pending_payments[transaction_id]
        
        if payment['status'] == 'completed':
            return False, "Transaction already completed"
        
        # In production, verify with blockchain API
        # For now, mark as pending verification
        payment['tx_hash'] = tx_hash
        payment['status'] = 'pending_verification'
        
        return True, "Crypto payment recorded. Admin will verify and activate premium."
    
    def confirm_payment(self, transaction_id: str, admin_id: int) -> Tuple[bool, str]:
        """Admin confirm payment and activate premium"""
        if transaction_id not in self.pending_payments:
            return False, "Transaction not found"
        
        if admin_id not in Config.ADMIN_IDS:
            return False, "Unauthorized"
        
        payment = self.pending_payments[transaction_id]
        
        if payment['status'] == 'completed':
            return False, "Transaction already completed"
        
        # Map plan to PremiumPlan
        plan_map = {
            'monthly': PremiumPlan.MONTHLY,
            'yearly': PremiumPlan.YEARLY,
            'lifetime': PremiumPlan.LIFETIME
        }
        
        plan = plan_map.get(payment['plan'], PremiumPlan.MONTHLY)
        
        # Record in database
        db_transaction_id = self.generate_transaction_id(payment['user_id'])
        db.add_transaction(
            user_id=payment['user_id'],
            amount=payment['amount'],
            payment_method=payment['method'],
            transaction_id=db_transaction_id,
            plan_type=payment['plan'],
            duration_days=30 if payment['plan'] == 'monthly' else 365 if payment['plan'] == 'yearly' else 3650
        )
        
        # Activate premium
        premium_manager.activate_premium(
            payment['user_id'],
            plan,
            payment['method'],
            db_transaction_id
        )
        
        # Update status
        payment['status'] = 'completed'
        payment['verified_by'] = admin_id
        payment['verified_at'] = datetime.now().isoformat()
        
        return True, f"Premium {payment['plan']} activated for user {payment['user_id']}"
    
    # ============================================
    # PAYMENT STATUS
    # ============================================
    
    def get_payment_status(self, transaction_id: str, user_id: int) -> Optional[Dict]:
        """Get payment status"""
        if transaction_id not in self.pending_payments:
            return None
        
        payment = self.pending_payments[transaction_id]
        
        if payment['user_id'] != user_id:
            return None
        
        return {
            'transaction_id': transaction_id,
            'status': payment['status'],
            'amount': payment['amount'],
            'plan': payment['plan'],
            'method': payment['method'],
            'created_at': payment['created_at']
        }
    
    def get_user_pending_payments(self, user_id: int) -> list:
        """Get user's pending payments"""
        pending = []
        for tx_id, payment in self.pending_payments.items():
            if payment['user_id'] == user_id and payment['status'] == 'pending':
                pending.append({
                    'transaction_id': tx_id,
                    'amount': payment['amount'],
                    'plan': payment['plan'],
                    'method': payment['method'],
                    'created_at': payment['created_at']
                })
        return pending
    
    def cleanup_expired_payments(self, hours: int = 24):
        """Clean up expired pending payments"""
        now = datetime.now()
        expired = []
        
        for tx_id, payment in self.pending_payments.items():
            if payment['status'] == 'pending':
                created_at = datetime.fromisoformat(payment['created_at'])
                if (now - created_at).total_seconds() > hours * 3600:
                    expired.append(tx_id)
        
        for tx_id in expired:
            del self.pending_payments[tx_id]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired payments")
        
        return len(expired)
    
    # ============================================
    # INVOICE GENERATION
    # ============================================
    
    def generate_invoice(self, transaction_id: str, user_id: int) -> Optional[Dict]:
        """Generate invoice for completed payment"""
        # Get transaction from database
        transaction = db.get_transaction(transaction_id)
        
        if not transaction or transaction['user_id'] != user_id:
            return None
        
        if transaction['status'] != 'completed':
            return None
        
        user = db.get_user(user_id)
        
        invoice = {
            'invoice_no': f"INV-{transaction_id}",
            'date': transaction['completed_at'][:10],
            'user': {
                'id': user['id'],
                'username': user.get('username', 'N/A'),
                'name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            },
            'plan': transaction['plan_type'],
            'amount': transaction['amount'],
            'currency': 'USD',
            'payment_method': transaction['payment_method'],
            'status': 'Paid'
        }
        
        return invoice
    
    # ============================================
    # REFUND PROCESSING
    # ============================================
    
    def process_refund(self, transaction_id: str, admin_id: int, reason: str) -> Tuple[bool, str]:
        """Process refund (admin only)"""
        if admin_id not in Config.ADMIN_IDS:
            return False, "Unauthorized"
        
        transaction = db.get_transaction(transaction_id)
        
        if not transaction:
            return False, "Transaction not found"
        
        if transaction['status'] != 'completed':
            return False, "Transaction not completed"
        
        # Update transaction status
        db.conn.cursor().execute(
            "UPDATE transactions SET status = 'refunded' WHERE transaction_id = ?",
            (transaction_id,)
        )
        db.conn.commit()
        
        # Remove premium if within refund period
        user_id = transaction['user_id']
        premium_manager.cancel_premium(user_id)
        
        # Add notification
        db.add_notification(
            user_id,
            "Refund Processed 💰",
            f"Your payment of ${transaction['amount']} has been refunded.\n\nReason: {reason}\n\nFunds will reflect in 3-5 business days."
        )
        
        return True, f"Refund processed for {transaction_id}"
    
    # ============================================
    # PAYMENT METHODS INFO
    # ============================================
    
    def get_payment_methods(self) -> Dict:
        """Get available payment methods"""
        return {
            'upi': {
                'name': 'UPI (Google Pay, PhonePe, Paytm)',
                'icon': '💳',
                'available': True,
                'currency': 'INR',
                'instructions': f'Pay to {self.upi_id}'
            },
            'stars': {
                'name': 'Telegram Stars',
                'icon': '⭐',
                'available': True,
                'currency': 'Stars',
                'instructions': 'Instant activation after payment'
            },
            'paypal': {
                'name': 'PayPal',
                'icon': '💸',
                'available': bool(Config.PAYPAL_CLIENT_ID),
                'currency': 'USD',
                'instructions': 'Pay with PayPal account or credit card'
            },
            'crypto': {
                'name': 'Cryptocurrency (USDT/BTC)',
                'icon': '₿',
                'available': bool(Config.CRYPTO_WALLET_USDT),
                'currency': 'USDT/BTC',
                'instructions': 'Send crypto to wallet address'
            }
        }
    
    def get_payment_summary(self, plan: str) -> Dict:
        """Get payment summary for a plan"""
        prices = {
            'monthly': {
                'usd': Config.PREMIUM_PRICE_MONTHLY_USD,
                'inr': Config.PREMIUM_PRICE_MONTHLY_INR,
                'stars': Config.PREMIUM_PRICE_MONTHLY_STARS
            },
            'yearly': {
                'usd': Config.PREMIUM_PRICE_YEARLY_USD,
                'inr': Config.PREMIUM_PRICE_YEARLY_INR,
                'stars': Config.PREMIUM_PRICE_YEARLY_STARS
            },
            'lifetime': {
                'usd': Config.PREMIUM_PRICE_LIFETIME_USD,
                'inr': Config.PREMIUM_PRICE_LIFETIME_INR,
                'stars': Config.PREMIUM_PRICE_LIFETIME_STARS
            }
        }
        
        return prices.get(plan, prices['monthly'])


# ============================================
# INITIALIZE PAYMENT MANAGER
# ============================================

payment_manager = PaymentManager()
