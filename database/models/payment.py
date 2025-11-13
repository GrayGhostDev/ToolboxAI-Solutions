"""
Payment Database Models
Defines SQLAlchemy models for payment processing and subscription management

Multi-tenant: All models use organization_id for tenant isolation
@module payment
@version 2.0.0
@since 2025-09-26
@updated 2025-10-10 (Added multi-tenant support)
"""

from enum import Enum

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import tenant-aware base models
from database.models.base import TenantBaseModel


# Enums
class PaymentStatus(str, Enum):
    """Payment status enum"""

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class SubscriptionStatus(str, Enum):
    """Subscription status enum"""

    TRIALING = "trialing"
    ACTIVE = "active"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class SubscriptionTier(str, Enum):
    """Subscription tier enum"""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PaymentMethod(str, Enum):
    """Payment method types"""

    CARD = "card"
    BANK_ACCOUNT = "bank_account"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    CRYPTO = "crypto"


class InvoiceStatus(str, Enum):
    """Invoice status enum"""

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    VOIDED = "voided"
    UNCOLLECTIBLE = "uncollectible"


# Models
class Customer(TenantBaseModel):
    """
    Customer model - Maps internal users to payment provider customers

    Multi-tenant: organization_id inherited from TenantBaseModel
    Note: Uses Integer ID for backwards compatibility (overrides UUID default)
    """

    __tablename__ = "customers"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255))
    currency = Column(String(3), default="usd")

    # Customer details
    balance = Column(Numeric(10, 2), default=0)
    credit_balance = Column(Numeric(10, 2), default=0)
    invoice_prefix = Column(String(10))
    tax_exempt = Column(Boolean, default=False)
    tax_id = Column(String(50))

    # Settings
    default_payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    auto_collection = Column(Boolean, default=True)
    invoice_settings = Column(JSON)

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)

    # Note: created_at, updated_at timestamps inherited from TenantBaseModel

    # Relationships
    user = relationship("User", back_populates="customer")
    subscriptions = relationship(
        "Subscription", back_populates="customer", cascade="all, delete-orphan"
    )
    payment_methods = relationship(
        "CustomerPaymentMethod", back_populates="customer", cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="customer", cascade="all, delete-orphan")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_customer_org_user", "organization_id", "user_id"),
        Index("idx_customer_org_stripe", "organization_id", "stripe_customer_id"),
    )


class Subscription(TenantBaseModel):
    """
    Subscription model - Manages recurring billing subscriptions

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "subscriptions"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)

    # Subscription details
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.INCOMPLETE)
    tier = Column(SQLEnum(SubscriptionTier), default=SubscriptionTier.FREE)
    price_id = Column(String(255))  # Stripe price ID
    quantity = Column(Integer, default=1)

    # Billing
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    interval = Column(String(20))  # monthly, yearly, etc.
    interval_count = Column(Integer, default=1)

    # Period
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    billing_cycle_anchor = Column(DateTime(timezone=True))

    # Trial
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))

    # Cancellation
    cancel_at = Column(DateTime(timezone=True))
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(String(255))

    # Pause
    pause_collection = Column(JSON)  # Pause collection settings

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)

    # Additional timestamps (created_at, updated_at inherited from TenantBaseModel)
    ended_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="subscriptions")
    subscription_items = relationship(
        "SubscriptionItem", back_populates="subscription", cascade="all, delete-orphan"
    )
    usage_records = relationship(
        "UsageRecord", back_populates="subscription", cascade="all, delete-orphan"
    )

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_subscription_org_customer", "organization_id", "customer_id"),
        Index("idx_subscription_org_status", "organization_id", "status"),
        Index("idx_subscription_org_tier", "organization_id", "tier"),
        Index("idx_subscription_stripe", "stripe_subscription_id"),
    )


class SubscriptionItem(TenantBaseModel):
    """
    Subscription Item model - Individual items within a subscription

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "subscription_items"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    stripe_subscription_item_id = Column(String(255), unique=True, index=True)

    # Item details
    price_id = Column(String(255), nullable=False)  # Stripe price ID
    product_id = Column(String(255))  # Stripe product ID
    quantity = Column(Integer, default=1)

    # Pricing
    unit_amount = Column(Numeric(10, 2))
    tax_rates = Column(JSON)

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)

    # Relationships
    subscription = relationship("Subscription", back_populates="subscription_items")


class CustomerPaymentMethod(TenantBaseModel):
    """
    Payment Method model - Stores customer payment methods

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "payment_methods"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    stripe_payment_method_id = Column(String(255), unique=True, index=True)

    # Method details
    type = Column(SQLEnum(PaymentMethod), default=PaymentMethod.CARD)
    is_default = Column(Boolean, default=False)

    # Card details (if applicable)
    card_brand = Column(String(20))  # visa, mastercard, amex, etc.
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    card_fingerprint = Column(String(255))

    # Bank details (if applicable)
    bank_name = Column(String(255))
    bank_last4 = Column(String(4))
    bank_routing_number = Column(String(20))

    # Billing details
    billing_name = Column(String(255))
    billing_email = Column(String(255))
    billing_phone = Column(String(50))
    billing_address = Column(JSON)

    # Status
    status = Column(String(20))  # active, inactive, expired

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)

    # Note: created_at, updated_at timestamps inherited from TenantBaseModel

    # Relationships
    customer = relationship("Customer", back_populates="payment_methods")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_payment_method_org_customer", "organization_id", "customer_id"),
        Index("idx_payment_method_stripe", "stripe_payment_method_id"),
        Index("idx_payment_method_org_default", "organization_id", "customer_id", "is_default"),
    )


class Payment(TenantBaseModel):
    """
    Payment model - Records all payment transactions

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "payments"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))

    # Stripe IDs
    stripe_payment_intent_id = Column(String(255), unique=True, index=True)
    stripe_charge_id = Column(String(255), unique=True, index=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)

    # Fees
    application_fee_amount = Column(Numeric(10, 2))
    processing_fee = Column(Numeric(10, 2))
    net_amount = Column(Numeric(10, 2))

    # Refund info
    refunded = Column(Boolean, default=False)
    refunded_amount = Column(Numeric(10, 2), default=0)
    refund_reason = Column(String(255))

    # Payment method details
    payment_method_type = Column(String(50))
    last4 = Column(String(4))
    brand = Column(String(20))

    # Additional info
    description = Column(Text)
    statement_descriptor = Column(String(22))
    receipt_email = Column(String(255))
    receipt_url = Column(String(500))

    # Risk assessment
    risk_level = Column(String(20))
    risk_score = Column(Integer)

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)
    failure_code = Column(String(50))
    failure_message = Column(String(500))

    # Additional timestamps (created_at, updated_at inherited from TenantBaseModel)
    paid_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="payments")
    payment_method = relationship("CustomerPaymentMethod")
    invoice = relationship("Invoice", back_populates="payments")
    subscription = relationship("Subscription")
    refunds = relationship("Refund", back_populates="payment", cascade="all, delete-orphan")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_payment_org_customer", "organization_id", "customer_id"),
        Index("idx_payment_org_status", "organization_id", "status"),
        Index("idx_payment_org_created", "organization_id", "created_at"),
        Index("idx_payment_stripe_intent", "stripe_payment_intent_id"),
        Index("idx_payment_stripe_charge", "stripe_charge_id"),
    )


class Invoice(TenantBaseModel):
    """
    Invoice model - Billing invoices for subscriptions and one-time charges

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "invoices"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    stripe_invoice_id = Column(String(255), unique=True, index=True)

    # Invoice details
    number = Column(String(50), unique=True, index=True)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.DRAFT)

    # Amounts
    subtotal = Column(Numeric(10, 2), nullable=False)
    tax = Column(Numeric(10, 2), default=0)
    total = Column(Numeric(10, 2), nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    amount_remaining = Column(Numeric(10, 2))
    currency = Column(String(3), default="usd")

    # Discount
    discount_amount = Column(Numeric(10, 2), default=0)
    discount_percentage = Column(Numeric(5, 2))
    coupon_code = Column(String(50))

    # Period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Due date
    due_date = Column(DateTime(timezone=True))

    # Payment
    attempted = Column(Boolean, default=False)
    attempt_count = Column(Integer, default=0)
    next_payment_attempt = Column(DateTime(timezone=True))

    # URLs
    hosted_invoice_url = Column(String(500))
    invoice_pdf = Column(String(500))

    # Metadata
    description = Column(Text)
    footer = Column(Text)
    memo = Column(Text)
    invoice_metadata = Column(JSON)

    # Additional timestamps (created_at, updated_at inherited from TenantBaseModel)
    paid_at = Column(DateTime(timezone=True))
    voided_at = Column(DateTime(timezone=True))
    finalized_at = Column(DateTime(timezone=True))

    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    subscription = relationship("Subscription")
    invoice_items = relationship(
        "InvoiceItem", back_populates="invoice", cascade="all, delete-orphan"
    )
    payments = relationship("Payment", back_populates="invoice")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_invoice_org_customer", "organization_id", "customer_id"),
        Index("idx_invoice_org_subscription", "organization_id", "subscription_id"),
        Index("idx_invoice_org_status", "organization_id", "status"),
        Index("idx_invoice_number", "number"),
        Index("idx_invoice_stripe", "stripe_invoice_id"),
        Index("idx_invoice_org_due", "organization_id", "due_date"),
    )


class InvoiceItem(TenantBaseModel):
    """
    Invoice Item model - Line items on an invoice

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "invoice_items"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at inherited from TenantBaseModel

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    stripe_invoice_item_id = Column(String(255), unique=True, index=True)

    # Item details
    description = Column(String(500))
    quantity = Column(Integer, default=1)
    unit_amount = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")

    # Product/Price reference
    price_id = Column(String(255))
    product_id = Column(String(255))

    # Period
    period_start = Column(DateTime(timezone=True))
    period_end = Column(DateTime(timezone=True))

    # Tax
    tax_amounts = Column(JSON)

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)

    # Relationships
    invoice = relationship("Invoice", back_populates="invoice_items")


class Refund(TenantBaseModel):
    """
    Refund model - Tracks refund transactions

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "refunds"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at, updated_at inherited from TenantBaseModel

    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)
    stripe_refund_id = Column(String(255), unique=True, index=True)

    # Refund details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(20))  # pending, succeeded, failed, canceled
    reason = Column(String(255))

    # Receipt
    receipt_number = Column(String(50))

    # Metadata (renamed from 'metadata' to avoid SQLAlchemy reserved word)
    payment_metadata = Column(JSON)
    failure_reason = Column(String(255))

    # Relationships
    payment = relationship("Payment", back_populates="refunds")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_refund_org_payment", "organization_id", "payment_id"),
        Index("idx_refund_stripe", "stripe_refund_id"),
    )


class UsageRecord(TenantBaseModel):
    """
    Usage Record model - Tracks metered billing usage

    Multi-tenant: organization_id inherited from TenantBaseModel
    """

    __tablename__ = "usage_records"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Note: organization_id, created_at inherited from TenantBaseModel

    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)

    # Usage details
    quantity = Column(Integer, nullable=False)
    action = Column(String(20))  # increment, set
    timestamp = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    description = Column(String(500))
    usage_metadata = Column(JSON)

    # Relationships
    subscription = relationship("Subscription", back_populates="usage_records")

    # Constraints and indexes (organization_id index auto-created by TenantMixin)
    __table_args__ = (
        Index("idx_usage_org_subscription", "organization_id", "subscription_id"),
        Index("idx_usage_org_timestamp", "organization_id", "timestamp"),
    )


class Coupon(TenantBaseModel):
    """
    Coupon model - Discount coupons for subscriptions

    Multi-tenant: organization_id inherited from TenantBaseModel
    Special: Allows nullable organization_id for platform-wide coupons
    """

    __tablename__ = "coupons"

    # Override id to use Integer for backwards compatibility
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Override organization_id to be nullable for platform-wide coupons
    # NULL = platform-wide coupon, value = organization-specific coupon
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,  # Platform-wide coupons have NULL
        index=True,
    )

    # Note: created_at, updated_at inherited from TenantBaseModel

    code = Column(String(50), unique=True, nullable=False, index=True)
    stripe_coupon_id = Column(String(255), unique=True, index=True)

    # Discount details
    amount_off = Column(Numeric(10, 2))  # Fixed amount discount
    percent_off = Column(Numeric(5, 2))  # Percentage discount
    currency = Column(String(3))

    # Duration
    duration = Column(String(20))  # forever, once, repeating
    duration_in_months = Column(Integer)

    # Restrictions
    max_redemptions = Column(Integer)
    times_redeemed = Column(Integer, default=0)

    # Validity
    valid = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # Metadata
    name = Column(String(255))
    coupon_metadata = Column(JSON)

    # Constraints and indexes
    __table_args__ = (
        Index("idx_coupon_code", "code"),
        Index("idx_coupon_org_valid", "organization_id", "valid"),
        Index("idx_coupon_validity_period", "valid_from", "valid_until"),
    )
