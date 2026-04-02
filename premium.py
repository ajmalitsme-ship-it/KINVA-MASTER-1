# ============================================
# PREMIUM.PY - COMPLETE PREMIUM MANAGEMENT SYSTEM
# KINVA MASTER PRO - SUBSCRIPTION & FEATURES
# ============================================

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from config import Config
from database import db

logger = logging.getLogger(__name__)


class PremiumPlan(Enum):
    """Premium plan types"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LIFETIME = "lifetime"


class PremiumManager:
    """Complete Premium Management System"""
    
    def __init__(self):
        self.plans = {
            PremiumPlan.MONTHLY: {
                'name': 'Monthly Premium',
                'days': 30,
                'price_usd': Config.PREMIUM_PRICE_MONTHLY_USD,
                'price_inr': Config.PREMIUM_PRICE_MONTHLY_INR,
                'price_stars': Config.PREMIUM_PRICE_MONTHLY_STARS,
                'features': self._get_monthly_features()
            },
            PremiumPlan.YEARLY: {
                'name': 'Yearly Premium',
                'days': 365,
                'price_usd': Config.PREMIUM_PRICE_YEARLY_USD,
                'price_inr': Config.PREMIUM_PRICE_YEARLY_INR,
                'price_stars': Config.PREMIUM_PRICE_YEARLY_STARS,
                'features': self._get_yearly_features()
            },
            PremiumPlan.LIFETIME: {
                'name': 'Lifetime Premium',
                'days': 365 * 10,  # 10 years
                'price_usd': Config.PREMIUM_PRICE_LIFETIME_USD,
                'price_inr': Config.PREMIUM_PRICE_LIFETIME_INR,
                'price_stars': Config.PREMIUM_PRICE_LIFETIME_STARS,
                'features': self._get_lifetime_features()
            }
        }
    
    def _get_monthly_features(self) -> Dict:
        """Get monthly premium features"""
        return {
            'file_size_limit_mb': Config.PREMIUM_MAX_FILE_SIZE_MB,
            'video_duration_limit': Config.PREMIUM_MAX_VIDEO_DURATION,
            'daily_edits': Config.PREMIUM_DAILY_EDITS,
            'watermark': False,
            'export_quality': '4K',
            'all_filters': True,
            'all_effects': True,
            'all_transitions': True,
            'motion_tracking': True,
            'chroma_key': True,
            'auto_captions': True,
            'background_removal': True,
            'voiceover': True,
            'priority_processing': True,
            'batch_processing': True,
            'advanced_export': True,
            'cloud_backup': True
        }
    
    def _get_yearly_features(self) -> Dict:
        """Get yearly premium features (includes extra benefits)"""
        features = self._get_monthly_features()
        features.update({
            'bonus_stars': 500,
            'free_months': 2,  # 2 months free
            'priority_support': True,
            'exclusive_templates': True,
            'early_access': True
        })
        return features
    
    def _get_lifetime_features(self) -> Dict:
        """Get lifetime premium features"""
        features = self._get_yearly_features()
        features.update({
            'bonus_stars': 2000,
            'free_updates': True,
            'featured_creator': True,
            'api_access': True,
            'custom_branding': True,
            'dedicated_support': True
        })
        return features
    
    # ============================================
    # PREMIUM CHECKING METHODS
    # ============================================
    
    def is_premium(self, user_id: int) -> bool:
        """Check if user has active premium"""
        return db.is_premium(user_id)
    
    def get_premium_status(self, user_id: int) -> Dict:
        """Get detailed premium status"""
        user = db.get_user(user_id)
        if not user:
            return {'is_premium': False, 'plan': None, 'expiry': None}
        
        is_premium = db.is_premium(user_id)
        
        if is_premium:
            expiry = datetime.fromisoformat(user['premium_expiry'])
            days_left = (expiry - datetime.now()).days
            
            return {
                'is_premium': True,
                'plan': user.get('premium_type', 'monthly'),
                'expiry': user['premium_expiry'],
                'days_left': days_left,
                'expired_soon': days_left <= 7
            }
        else:
            return {'is_premium': False, 'plan': None, 'expiry': None, 'days_left': 0}
    
    def get_premium_features(self, user_id: int) -> Dict:
        """Get features available to user"""
        if self.is_premium(user_id):
            user = db.get_user(user_id)
            plan_type = user.get('premium_type', 'monthly')
            
            try:
                plan = PremiumPlan(plan_type)
                return self.plans[plan]['features']
            except:
                return self.plans[PremiumPlan.MONTHLY]['features']
        else:
            return self._get_free_features()
    
    def _get_free_features(self) -> Dict:
        """Get free tier features"""
        return {
            'file_size_limit_mb': Config.FREE_MAX_FILE_SIZE_MB,
            'video_duration_limit': Config.FREE_MAX_VIDEO_DURATION,
            'daily_edits': Config.FREE_DAILY_EDITS,
            'watermark': True,
            'export_quality': '720p',
            'all_filters': False,
            'all_effects': False,
            'all_transitions': False,
            'motion_tracking': False,
            'chroma_key': False,
            'auto_captions': False,
            'background_removal': False,
            'voiceover': False,
            'priority_processing': False,
            'batch_processing': False,
            'advanced_export': False,
            'cloud_backup': False
        }
    
    # ============================================
    # PREMIUM ACTIVATION METHODS
    # ============================================
    
    def activate_premium(self, user_id: int, plan: PremiumPlan, 
                         payment_method: str = None, transaction_id: str = None) -> bool:
        """Activate premium for user"""
        try:
            plan_data = self.plans[plan]
            days = plan_data['days']
            
            # Add premium to database
            success = db.add_premium(user_id, days, plan.value)
            
            if success and transaction_id:
                # Record transaction
                db.add_transaction(
                    user_id=user_id,
                    amount=plan_data['price_usd'],
                    payment_method=payment_method,
                    transaction_id=transaction_id,
                    stars_amount=plan_data.get('price_stars'),
                    plan_type=plan.value,
                    duration_days=days
                )
                db.complete_transaction(transaction_id)
            
            # Add notification
            db.add_notification(
                user_id,
                "Premium Activated! 🎉",
                f"Your {plan_data['name']} has been activated successfully!\n\n"
                f"Features unlocked:\n"
                f"• 4GB File Support\n"
                f"• 60 Minute Videos\n"
                f"• No Watermark\n"
                f"• 4K Export\n"
                f"• All Filters & Effects\n\n"
                f"Thank you for supporting Kinva Master Pro!"
            )
            
            logger.info(f"Premium activated for user {user_id} with plan {plan.value}")
            return True
            
        except Exception as e:
            logger.error(f"Premium activation error: {e}")
            return False
    
    def extend_premium(self, user_id: int, days: int, reason: str = "admin_grant") -> bool:
        """Extend existing premium (admin only)"""
        user = db.get_user(user_id)
        if not user:
            return False
        
        current_expiry = user.get('premium_expiry')
        now = datetime.now()
        
        if current_expiry:
            try:
                expiry = datetime.fromisoformat(current_expiry)
                if expiry > now:
                    new_expiry = expiry + timedelta(days=days)
                else:
                    new_expiry = now + timedelta(days=days)
            except:
                new_expiry = now + timedelta(days=days)
        else:
            new_expiry = now + timedelta(days=days)
        
        return db.update_user(user_id, premium_expiry=new_expiry.isoformat())
    
    def cancel_premium(self, user_id: int) -> bool:
        """Cancel premium subscription"""
        user = db.get_user(user_id)
        if not user:
            return False
        
        success = db.update_user(user_id, is_premium=0, premium_expiry=None)
        
        if success:
            db.add_notification(
                user_id,
                "Premium Cancelled ❌",
                "Your premium subscription has been cancelled.\n\n"
                "You can resubscribe anytime using /premium"
            )
        
        return success
    
    # ============================================
    # PREMIUM CHECK METHODS FOR FEATURES
    # ============================================
    
    def can_upload_file(self, user_id: int, file_size_bytes: int) -> Tuple[bool, str]:
        """Check if user can upload file of given size"""
        is_premium = self.is_premium(user_id)
        max_size = Config.get_max_file_size_bytes(is_premium)
        
        if file_size_bytes > max_size:
            limit_mb = max_size // (1024 * 1024)
            return False, f"❌ File too large! Maximum {limit_mb}MB for {'premium' if is_premium else 'free'} users."
        
        return True, "OK"
    
    def can_process_video(self, user_id: int, duration_seconds: int) -> Tuple[bool, str]:
        """Check if user can process video of given duration"""
        is_premium = self.is_premium(user_id)
        max_duration = Config.get_max_duration(is_premium)
        
        if duration_seconds > max_duration:
            minutes = max_duration // 60
            return False, f"❌ Video too long! Maximum {minutes} minutes for {'premium' if is_premium else 'free'} users."
        
        return True, "OK"
    
    def can_edit_today(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can edit today"""
        if self.is_premium(user_id):
            return True, "Premium user - unlimited edits"
        
        user = db.get_user(user_id)
        if not user:
            return True, "New user"
        
        today = datetime.now().date().isoformat()
        
        if user.get('last_edit_date') != today:
            return True, "First edit of the day"
        
        edits_today = user.get('edits_today', 0)
        if edits_today < Config.FREE_DAILY_EDITS:
            remaining = Config.FREE_DAILY_EDITS - edits_today
            return True, f"Remaining edits today: {remaining}"
        
        return False, f"Daily limit reached! {Config.FREE_DAILY_EDITS}/{Config.FREE_DAILY_EDITS} edits used.\nUpgrade to premium for unlimited edits!"
    
    def has_feature(self, user_id: int, feature_name: str) -> bool:
        """Check if user has access to specific feature"""
        features = self.get_premium_features(user_id)
        return features.get(feature_name, False)
    
    # ============================================
    # PREMIUM STATISTICS
    # ============================================
    
    def get_premium_stats(self) -> Dict:
        """Get premium statistics"""
        premium_users = db.get_premium_users()
        total_premium = len(premium_users)
        
        plan_counts = {
            'monthly': 0,
            'yearly': 0,
            'lifetime': 0
        }
        
        expiring_soon = 0
        now = datetime.now()
        
        for user in premium_users:
            plan = user.get('premium_type', 'monthly')
            if plan in plan_counts:
                plan_counts[plan] += 1
            
            expiry = datetime.fromisoformat(user['premium_expiry'])
            if (expiry - now).days <= 7:
                expiring_soon += 1
        
        return {
            'total_premium': total_premium,
            'monthly': plan_counts['monthly'],
            'yearly': plan_counts['yearly'],
            'lifetime': plan_counts['lifetime'],
            'expiring_soon': expiring_soon
        }
    
    def get_revenue_stats(self) -> Dict:
        """Get revenue statistics"""
        cursor = db.conn.cursor()
        
        # Total revenue
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed'")
        total_revenue = cursor.fetchone()[0] or 0
        
        # Monthly revenue (last 30 days)
        month_ago = (datetime.now() - timedelta(days=30)).isoformat()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed' AND created_at > ?", (month_ago,))
        monthly_revenue = cursor.fetchone()[0] or 0
        
        # Today's revenue
        today = datetime.now().date().isoformat()
        cursor.execute("SELECT SUM(amount) FROM transactions WHERE status = 'completed' AND date(created_at) = ?", (today,))
        today_revenue = cursor.fetchone()[0] or 0
        
        # Payment method breakdown
        cursor.execute("""
            SELECT payment_method, COUNT(*), SUM(amount) 
            FROM transactions 
            WHERE status = 'completed' 
            GROUP BY payment_method
        """)
        payment_breakdown = cursor.fetchall()
        
        return {
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'today_revenue': today_revenue,
            'payment_breakdown': [
                {'method': row[0], 'count': row[1], 'amount': row[2]} 
                for row in payment_breakdown
            ]
        }
    
    # ============================================
    # PREMIUM MESSAGES
    # ============================================
    
    def get_premium_info_text(self, user_id: int) -> str:
        """Get premium info text for user"""
        status = self.get_premium_status(user_id)
        
        if status['is_premium']:
            return f"""
⭐ **YOUR PREMIUM STATUS** ⭐

━━━━━━━━━━━━━━━━━━━━━━
✨ **Plan:** {status['plan'].upper()}
📅 **Expires:** {status['expiry'][:10]}
⏰ **Days Left:** {status['days_left']}

✅ **Active Features:**
• 4GB File Support
• 60 Minute Videos
• No Watermark
• 4K Export
• 100+ Filters
• 50+ Effects
• Motion Tracking
• Chroma Key
• Auto Captions
• Priority Processing

{f"⚠️ **Your premium expires in {status['days_left']} days!** Renew now to continue enjoying benefits." if status['expired_soon'] else ""}

💎 Thank you for supporting Kinva Master Pro!
            """
        else:
            return self.get_upgrade_text()
    
    def get_upgrade_text(self) -> str:
        """Get upgrade promotion text"""
        return f"""
⭐ **UPGRADE TO PREMIUM** ⭐

━━━━━━━━━━━━━━━━━━━━━━
🚀 **Unlock Everything!**

**FREE vs PREMIUM:**

| Feature | FREE | PREMIUM |
|---------|------|---------|
| File Size | 700MB | **4GB** |
| Duration | 5 min | **60 min** |
| Daily Edits | 10 | **Unlimited** |
| Watermark | Yes | **No** |
| Export | 720p | **4K** |
| Filters | 10 | **100+** |
| Effects | 10 | **50+** |
| Motion Track | ❌ | **✅** |
| Chroma Key | ❌ | **✅** |
| Auto Captions | ❌ | **✅** |

━━━━━━━━━━━━━━━━━━━━━━
💎 **PLANS:**

• **Monthly:** ${Config.PREMIUM_PRICE_MONTHLY_USD} / ₹{Config.PREMIUM_PRICE_MONTHLY_INR}
• **Yearly:** ${Config.PREMIUM_PRICE_YEARLY_USD} / ₹{Config.PREMIUM_PRICE_YEARLY_INR} (Save 50%)
• **Lifetime:** ${Config.PREMIUM_PRICE_LIFETIME_USD} / ₹{Config.PREMIUM_PRICE_LIFETIME_INR}

━━━━━━━━━━━━━━━━━━━━━━
💳 **Payment Methods:**
• UPI: `{Config.UPI_ID}`
• Telegram Stars
• PayPal
• Credit/Debit Card

🔥 **Upgrade now and get 7 days free!**
        """
    
    def get_comparison_text(self) -> str:
        """Get detailed comparison between plans"""
        return """
📊 **PLAN COMPARISON**

━━━━━━━━━━━━━━━━━━━━━━
**FREE PLAN:**
• 700MB file limit
• 5 minute videos
• 10 edits/day
• Watermark included
• 720p export
• 10 basic filters
• Basic effects

━━━━━━━━━━━━━━━━━━━━━━
**PREMIUM MONTHLY:**
• 4GB file limit
• 60 minute videos
• Unlimited edits
• No watermark
• 4K export
• 100+ filters
• 50+ effects
• Motion tracking
• Chroma key
• Auto captions

━━━━━━━━━━━━━━━━━━━━━━
**PREMIUM YEARLY:**
• All monthly features
• 2 months free
• 500 bonus stars
• Priority support
• Exclusive templates

━━━━━━━━━━━━━━━━━━━━━━
**PREMIUM LIFETIME:**
• All yearly features
• Lifetime access
• 2000 bonus stars
• API access
• Custom branding
• Featured creator status
        """


# ============================================
# INITIALIZE PREMIUM MANAGER
# ============================================

premium_manager = PremiumManager()
