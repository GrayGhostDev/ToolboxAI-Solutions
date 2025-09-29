"""
Invoice Generation Service
Handles invoice creation, PDF generation, and management
Following 2025 best practices for billing and invoicing
@module invoice_generator
@version 1.0.0
@since 2025-09-27
"""

import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from decimal import Decimal
import json
import uuid
from io import BytesIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from apps.backend.core.config import settings
from apps.backend.services.stripe_service import stripe_service
from apps.backend.services.email_service import email_service
from database.models.payment import (
    Customer,
    Subscription,
    Invoice,
    InvoiceItem,
    Payment,
    InvoiceStatus,
    SubscriptionStatus
)
from database.connection import get_db

logger = logging.getLogger(__name__)

# Try to import PDF generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, Image, PageBreak
    )
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    PDF_GENERATION_AVAILABLE = True
except ImportError:
    PDF_GENERATION_AVAILABLE = False
    logger.warning("PDF generation not available. Install reportlab: pip install reportlab")


class InvoiceGenerator:
    """
    Service for generating and managing invoices
    Supports multiple formats and automatic Stripe synchronization
    """

    def __init__(self):
        """Initialize invoice generator with configuration"""
        self.company_name = getattr(settings, 'COMPANY_NAME', 'ToolBoxAI')
        self.company_address = getattr(settings, 'COMPANY_ADDRESS', '')
        self.company_email = getattr(settings, 'COMPANY_EMAIL', 'billing@toolboxai.com')
        self.invoice_prefix = getattr(settings, 'INVOICE_PREFIX', 'INV')
        self.tax_rate = Decimal(str(getattr(settings, 'DEFAULT_TAX_RATE', 0.0)))

    async def create_invoice(
        self,
        customer_id: int,
        subscription_id: Optional[int] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        db: AsyncSession = None,
        send_email: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new invoice for a customer

        Args:
            customer_id: Customer ID
            subscription_id: Optional subscription ID
            items: List of invoice items
            db: Database session
            send_email: Whether to send invoice email

        Returns:
            Created invoice data
        """
        try:
            # Get customer
            customer_query = select(Customer).where(Customer.id == customer_id)
            customer = await db.execute(customer_query)
            customer = customer.scalar_one_or_none()

            if not customer:
                raise ValueError(f"Customer {customer_id} not found")

            # Generate invoice number
            invoice_number = await self._generate_invoice_number(db)

            # Calculate amounts
            subtotal = Decimal("0")
            tax = Decimal("0")
            invoice_items = []

            # Process subscription if provided
            if subscription_id:
                subscription_query = select(Subscription).where(
                    Subscription.id == subscription_id
                ).options(selectinload(Subscription.subscription_items))
                subscription = await db.execute(subscription_query)
                subscription = subscription.scalar_one_or_none()

                if subscription:
                    # Add subscription items
                    for sub_item in subscription.subscription_items:
                        item_amount = sub_item.unit_amount * sub_item.quantity
                        subtotal += item_amount

                        invoice_item = InvoiceItem(
                            description=f"Subscription - {subscription.tier}",
                            quantity=sub_item.quantity,
                            unit_amount=sub_item.unit_amount,
                            amount=item_amount,
                            metadata={"subscription_item_id": sub_item.id}
                        )
                        invoice_items.append(invoice_item)

            # Process additional items
            if items:
                for item in items:
                    item_amount = Decimal(str(item.get('amount', 0)))
                    quantity = item.get('quantity', 1)
                    unit_amount = item_amount / quantity

                    subtotal += item_amount

                    invoice_item = InvoiceItem(
                        description=item.get('description', 'Service'),
                        quantity=quantity,
                        unit_amount=unit_amount,
                        amount=item_amount,
                        metadata=item.get('metadata', {})
                    )
                    invoice_items.append(invoice_item)

            # Calculate tax
            if self.tax_rate > 0:
                tax = subtotal * (self.tax_rate / 100)

            total = subtotal + tax

            # Create invoice
            invoice = Invoice(
                customer_id=customer_id,
                subscription_id=subscription_id,
                number=invoice_number,
                status=InvoiceStatus.DRAFT,
                subtotal=subtotal,
                tax=tax,
                total=total,
                amount_due=total,
                amount_paid=Decimal("0"),
                amount_remaining=total,
                currency="usd",
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc) + timedelta(days=30),
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
                metadata={
                    "generated_by": "invoice_generator",
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
            )

            db.add(invoice)
            await db.flush()

            # Add invoice items
            for item in invoice_items:
                item.invoice_id = invoice.id
                db.add(item)

            # Create in Stripe if customer has Stripe ID
            if customer.stripe_customer_id:
                stripe_invoice = await self._create_stripe_invoice(
                    customer=customer,
                    invoice=invoice,
                    items=invoice_items
                )

                if stripe_invoice:
                    invoice.stripe_invoice_id = stripe_invoice.get('id')
                    invoice.hosted_invoice_url = stripe_invoice.get('hosted_invoice_url')
                    invoice.invoice_pdf = stripe_invoice.get('invoice_pdf')

            await db.commit()

            # Generate PDF
            if PDF_GENERATION_AVAILABLE:
                pdf_bytes = await self.generate_invoice_pdf(invoice.id, db)
                # Store PDF (would upload to storage in production)
                invoice.metadata["pdf_generated"] = True

            # Send email if requested
            if send_email:
                await self._send_invoice_email(invoice, customer)

            logger.info(f"Created invoice {invoice.number} for customer {customer_id}")

            return {
                "success": True,
                "invoice_id": invoice.id,
                "invoice_number": invoice.number,
                "total": float(total),
                "due_date": invoice.due_date.isoformat(),
                "hosted_url": invoice.hosted_invoice_url
            }

        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            if db:
                await db.rollback()
            return {"success": False, "error": str(e)}

    async def finalize_invoice(
        self,
        invoice_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Finalize a draft invoice

        Args:
            invoice_id: Invoice ID
            db: Database session

        Returns:
            Finalization result
        """
        try:
            # Get invoice
            invoice_query = select(Invoice).where(
                Invoice.id == invoice_id
            ).options(
                selectinload(Invoice.customer),
                selectinload(Invoice.invoice_items)
            )
            invoice = await db.execute(invoice_query)
            invoice = invoice.scalar_one_or_none()

            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            if invoice.status != InvoiceStatus.DRAFT:
                raise ValueError(f"Invoice {invoice_id} is not a draft")

            # Update status
            invoice.status = InvoiceStatus.OPEN
            invoice.finalized_at = datetime.now(timezone.utc)

            # Finalize in Stripe
            if invoice.stripe_invoice_id:
                stripe_invoice = stripe.Invoice.finalize_invoice(
                    invoice.stripe_invoice_id
                )
                invoice.hosted_invoice_url = stripe_invoice.hosted_invoice_url
                invoice.invoice_pdf = stripe_invoice.invoice_pdf

            await db.commit()

            # Send invoice email
            await self._send_invoice_email(invoice, invoice.customer)

            logger.info(f"Finalized invoice {invoice.number}")

            return {
                "success": True,
                "invoice_id": invoice.id,
                "status": invoice.status,
                "hosted_url": invoice.hosted_invoice_url
            }

        except Exception as e:
            logger.error(f"Error finalizing invoice: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def generate_invoice_pdf(
        self,
        invoice_id: int,
        db: AsyncSession
    ) -> Optional[bytes]:
        """
        Generate PDF for an invoice

        Args:
            invoice_id: Invoice ID
            db: Database session

        Returns:
            PDF bytes or None
        """
        if not PDF_GENERATION_AVAILABLE:
            logger.warning("PDF generation not available")
            return None

        try:
            # Get invoice with all related data
            invoice_query = select(Invoice).where(
                Invoice.id == invoice_id
            ).options(
                selectinload(Invoice.customer),
                selectinload(Invoice.invoice_items),
                selectinload(Invoice.subscription)
            )
            invoice = await db.execute(invoice_query)
            invoice = invoice.scalar_one_or_none()

            if not invoice:
                logger.error(f"Invoice {invoice_id} not found")
                return None

            # Create PDF buffer
            buffer = BytesIO()

            # Create PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )

            # Container for PDF elements
            elements = []
            styles = getSampleStyleSheet()

            # Company header
            company_style = ParagraphStyle(
                'CompanyStyle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#667eea'),
                alignment=TA_CENTER
            )
            elements.append(Paragraph(self.company_name, company_style))
            elements.append(Spacer(1, 0.5 * inch))

            # Invoice title
            title_style = ParagraphStyle(
                'InvoiceTitle',
                parent=styles['Heading1'],
                fontSize=20,
                alignment=TA_CENTER
            )
            elements.append(Paragraph("INVOICE", title_style))
            elements.append(Spacer(1, 0.3 * inch))

            # Invoice details
            invoice_info = [
                ['Invoice Number:', invoice.number],
                ['Invoice Date:', invoice.created_at.strftime('%B %d, %Y')],
                ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
                ['Status:', invoice.status.upper()]
            ]

            info_table = Table(invoice_info, colWidths=[2 * inch, 3 * inch])
            info_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Customer information
            customer_style = ParagraphStyle(
                'CustomerStyle',
                parent=styles['Heading2'],
                fontSize=14
            )
            elements.append(Paragraph("Bill To:", customer_style))
            elements.append(Spacer(1, 0.1 * inch))

            customer_info = [
                invoice.customer.name,
                invoice.customer.email
            ]
            for info in customer_info:
                elements.append(Paragraph(info, styles['Normal']))

            elements.append(Spacer(1, 0.3 * inch))

            # Invoice items table
            items_data = [['Description', 'Quantity', 'Unit Price', 'Amount']]

            for item in invoice.invoice_items:
                items_data.append([
                    item.description,
                    str(item.quantity),
                    f"${item.unit_amount:.2f}",
                    f"${item.amount:.2f}"
                ])

            items_table = Table(
                items_data,
                colWidths=[3 * inch, 1 * inch, 1.5 * inch, 1.5 * inch]
            )

            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            elements.append(items_table)
            elements.append(Spacer(1, 0.3 * inch))

            # Totals
            totals_data = []

            if invoice.tax > 0:
                totals_data.append(['Subtotal:', f"${invoice.subtotal:.2f}"])
                totals_data.append(['Tax:', f"${invoice.tax:.2f}"])

            totals_data.append(['Total:', f"${invoice.total:.2f}"])

            if invoice.amount_paid > 0:
                totals_data.append(['Paid:', f"${invoice.amount_paid:.2f}"])
                totals_data.append(['Amount Due:', f"${invoice.amount_due:.2f}"])

            totals_table = Table(
                totals_data,
                colWidths=[5 * inch, 1.5 * inch],
                hAlign='RIGHT'
            )

            totals_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ]))

            elements.append(totals_table)

            # Footer
            elements.append(Spacer(1, 0.5 * inch))
            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.gray,
                alignment=TA_CENTER
            )

            if invoice.footer:
                elements.append(Paragraph(invoice.footer, footer_style))
            else:
                elements.append(Paragraph(
                    f"Thank you for your business! Questions? Email {self.company_email}",
                    footer_style
                ))

            # Build PDF
            doc.build(elements)

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated PDF for invoice {invoice.number}")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}")
            return None

    async def _generate_invoice_number(self, db: AsyncSession) -> str:
        """Generate unique invoice number"""
        # Get last invoice number
        last_invoice_query = select(Invoice).order_by(Invoice.id.desc()).limit(1)
        result = await db.execute(last_invoice_query)
        last_invoice = result.scalar_one_or_none()

        if last_invoice and last_invoice.number:
            # Extract number and increment
            last_num = last_invoice.number.replace(self.invoice_prefix, '')
            try:
                next_num = int(last_num) + 1
            except:
                next_num = 1
        else:
            next_num = 1

        # Format with padding
        invoice_number = f"{self.invoice_prefix}{next_num:06d}"
        return invoice_number

    async def _create_stripe_invoice(
        self,
        customer: Customer,
        invoice: Invoice,
        items: List[InvoiceItem]
    ) -> Optional[Dict[str, Any]]:
        """Create invoice in Stripe"""
        try:
            import stripe

            # Create invoice
            stripe_invoice = stripe.Invoice.create(
                customer=customer.stripe_customer_id,
                auto_advance=False,  # Don't automatically charge
                collection_method="charge_automatically",
                description=f"Invoice {invoice.number}",
                metadata={
                    "invoice_id": str(invoice.id),
                    "invoice_number": invoice.number
                }
            )

            # Add invoice items
            for item in items:
                stripe.InvoiceItem.create(
                    customer=customer.stripe_customer_id,
                    invoice=stripe_invoice.id,
                    amount=int(item.amount * 100),  # Convert to cents
                    currency="usd",
                    description=item.description
                )

            # Finalize if not draft
            if invoice.status != InvoiceStatus.DRAFT:
                stripe_invoice = stripe.Invoice.finalize_invoice(stripe_invoice.id)

            return stripe_invoice.to_dict()

        except Exception as e:
            logger.error(f"Error creating Stripe invoice: {e}")
            return None

    async def _send_invoice_email(
        self,
        invoice: Invoice,
        customer: Customer
    ) -> None:
        """Send invoice email to customer"""
        try:
            # Generate or get PDF
            if PDF_GENERATION_AVAILABLE:
                # In production, this would attach the PDF
                pass

            await email_service.send_email(
                to_emails=customer.email,
                subject=f"Invoice {invoice.number} from {self.company_name}",
                template_name="invoice",
                template_context={
                    "customer_name": customer.name,
                    "invoice_number": invoice.number,
                    "total": float(invoice.total),
                    "due_date": invoice.due_date.strftime('%B %d, %Y'),
                    "view_invoice_url": invoice.hosted_invoice_url or f"{settings.FRONTEND_URL}/invoices/{invoice.id}",
                    "items": [
                        {
                            "description": item.description,
                            "quantity": item.quantity,
                            "amount": float(item.amount)
                        }
                        for item in invoice.invoice_items
                    ]
                }
            )

            logger.info(f"Sent invoice email for {invoice.number} to {customer.email}")

        except Exception as e:
            logger.error(f"Error sending invoice email: {e}")

    async def mark_invoice_paid(
        self,
        invoice_id: int,
        payment_id: int,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Mark an invoice as paid

        Args:
            invoice_id: Invoice ID
            payment_id: Payment ID
            db: Database session

        Returns:
            Update result
        """
        try:
            # Get invoice
            invoice_query = select(Invoice).where(Invoice.id == invoice_id)
            invoice = await db.execute(invoice_query)
            invoice = invoice.scalar_one_or_none()

            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")

            # Update invoice
            invoice.status = InvoiceStatus.PAID
            invoice.amount_paid = invoice.total
            invoice.amount_due = Decimal("0")
            invoice.amount_remaining = Decimal("0")
            invoice.paid_at = datetime.now(timezone.utc)

            # Update in Stripe
            if invoice.stripe_invoice_id:
                import stripe
                stripe.Invoice.pay(invoice.stripe_invoice_id)

            await db.commit()

            logger.info(f"Marked invoice {invoice.number} as paid")

            return {
                "success": True,
                "invoice_id": invoice.id,
                "status": invoice.status
            }

        except Exception as e:
            logger.error(f"Error marking invoice paid: {e}")
            await db.rollback()
            return {"success": False, "error": str(e)}


# Create singleton instance
invoice_generator = InvoiceGenerator()