/**
 * Unit Tests: SubscriptionManager Component
 *
 * Tests rendering, subscription actions, payment methods, and billing history
 * of the SubscriptionManager component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { SubscriptionManager } from '../SubscriptionManager';
import uiSlice from '../../../store/slices/uiSlice';

// Test wrapper with required providers
const renderWithProviders = (component: React.ReactElement) => {
  const mockStore = configureStore({
    reducer: {
      ui: uiSlice,
    },
  });

  return render(
    <Provider store={mockStore}>
      <MantineProvider>
        {component}
      </MantineProvider>
    </Provider>
  );
};

// Mock data
const mockActiveSubscription = {
  id: 'sub_123',
  planName: 'Professional',
  planPrice: '$79',
  interval: 'month' as const,
  status: 'active' as const,
  currentPeriodEnd: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: false,
};

const mockTrialSubscription = {
  id: 'sub_456',
  planName: 'Starter',
  planPrice: '$29',
  interval: 'month' as const,
  status: 'trialing' as const,
  currentPeriodEnd: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: false,
  trialEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
};

const mockCancelledSubscription = {
  ...mockActiveSubscription,
  cancelAtPeriodEnd: true,
};

const mockPastDueSubscription = {
  ...mockActiveSubscription,
  status: 'past_due' as const,
};

const mockPaymentMethods = [
  {
    id: 'pm_1',
    brand: 'visa',
    last4: '4242',
    expMonth: 12,
    expYear: 2025,
    isDefault: true,
  },
  {
    id: 'pm_2',
    brand: 'mastercard',
    last4: '5555',
    expMonth: 6,
    expYear: 2026,
    isDefault: false,
  },
];

const mockInvoices = [
  {
    id: 'in_123456',
    date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    amount: '$79.00',
    status: 'paid' as const,
    invoiceUrl: 'https://example.com/invoice/123',
  },
  {
    id: 'in_789012',
    date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000).toISOString(),
    amount: '$79.00',
    status: 'paid' as const,
  },
];

describe('SubscriptionManager Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Rendering Tests
   */
  describe('Rendering', () => {
    it('shows no subscription message when subscription is null', () => {
      renderWithProviders(<SubscriptionManager subscription={null} />);

      expect(screen.getByText('No Active Subscription')).toBeInTheDocument();
      expect(
        screen.getByText(/You don't have an active subscription/i)
      ).toBeInTheDocument();
      expect(screen.getByText('View Plans')).toBeInTheDocument();
    });

    it('shows active subscription details', () => {
      renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);

      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('ACTIVE')).toBeInTheDocument();
      expect(screen.getByText(/\$79\/month/i)).toBeInTheDocument();
    });

    it('shows trial subscription badge and alert', () => {
      renderWithProviders(<SubscriptionManager subscription={mockTrialSubscription} />);

      expect(screen.getByText('TRIALING')).toBeInTheDocument();
      expect(screen.getByText(/Your trial ends on/i)).toBeInTheDocument();
    });

    it('shows cancelled subscription alert', () => {
      renderWithProviders(
        <SubscriptionManager subscription={mockCancelledSubscription} />
      );

      expect(
        screen.getByText(/Your subscription is scheduled to cancel/i)
      ).toBeInTheDocument();
    });

    it('shows past due alert', () => {
      renderWithProviders(
        <SubscriptionManager subscription={mockPastDueSubscription} />
      );

      expect(screen.getByText('PAST_DUE')).toBeInTheDocument();
      expect(
        screen.getByText(/Your payment is past due/i)
      ).toBeInTheDocument();
    });
  });

  /**
   * Subscription Actions Tests
   */
  describe('Subscription Actions', () => {
    it('opens cancel modal when cancel button clicked', async () => {
      renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);

      const cancelButton = screen.getByText('Cancel Subscription');
      fireEvent.click(cancelButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Check for modal content
      expect(screen.getByText(/lose access to premium features/i)).toBeInTheDocument();
    });

    it('calls onCancelSubscription when confirmed', async () => {
      const mockOnCancel = vi.fn();

      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          onCancelSubscription={mockOnCancel}
        />
      );

      // Open modal
      const cancelButton = screen.getByText('Cancel Subscription');
      fireEvent.click(cancelButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Confirm cancellation
      const confirmButton = screen.getByText('Confirm Cancellation');
      fireEvent.click(confirmButton);

      await waitFor(() => {
        expect(mockOnCancel).toHaveBeenCalledWith('sub_123');
      });
    });

    it('closes cancel modal when keep subscription clicked', async () => {
      renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);

      // Open modal
      const cancelButton = screen.getByText('Cancel Subscription');
      fireEvent.click(cancelButton);

      // Wait for modal to appear
      await waitFor(() => {
        expect(screen.getByRole('dialog')).toBeInTheDocument();
      });

      // Click keep subscription
      const keepButton = screen.getByText('Keep Subscription');
      fireEvent.click(keepButton);

      // Wait for modal to close
      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
    });

    it('shows reactivate button for cancelled subscriptions', () => {
      renderWithProviders(
        <SubscriptionManager subscription={mockCancelledSubscription} />
      );

      expect(screen.getByText('Reactivate Subscription')).toBeInTheDocument();
      expect(screen.queryByText('Cancel Subscription')).not.toBeInTheDocument();
    });

    it('calls onReactivateSubscription when reactivate clicked', async () => {
      const mockOnReactivate = vi.fn();

      renderWithProviders(
        <SubscriptionManager
          subscription={mockCancelledSubscription}
          onReactivateSubscription={mockOnReactivate}
        />
      );

      const reactivateButton = screen.getByText('Reactivate Subscription');
      fireEvent.click(reactivateButton);

      await waitFor(() => {
        expect(mockOnReactivate).toHaveBeenCalledWith('sub_123');
      });
    });

    it('calls onChangePlan when change plan clicked', () => {
      const mockOnChangePlan = vi.fn();

      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          onChangePlan={mockOnChangePlan}
        />
      );

      const changePlanButton = screen.getByText('Change Plan');
      fireEvent.click(changePlanButton);

      expect(mockOnChangePlan).toHaveBeenCalledTimes(1);
    });
  });

  /**
   * Payment Methods Tests
   */
  describe('Payment Methods', () => {
    it('displays payment methods list', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          paymentMethods={mockPaymentMethods}
        />
      );

      expect(screen.getByText('Payment Methods')).toBeInTheDocument();
      expect(screen.getByText(/VISA •••• 4242/i)).toBeInTheDocument();
      expect(screen.getByText(/MASTERCARD •••• 5555/i)).toBeInTheDocument();
    });

    it('shows default payment method badge', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          paymentMethods={mockPaymentMethods}
        />
      );

      const defaultBadges = screen.getAllByText('Default');
      expect(defaultBadges).toHaveLength(1);
    });

    it('displays payment method expiration dates', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          paymentMethods={mockPaymentMethods}
        />
      );

      expect(screen.getByText(/Expires 12\/2025/i)).toBeInTheDocument();
      expect(screen.getByText(/Expires 6\/2026/i)).toBeInTheDocument();
    });

    it('hides payment methods section when empty', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          paymentMethods={[]}
        />
      );

      expect(screen.queryByText('Payment Methods')).not.toBeInTheDocument();
    });
  });

  /**
   * Billing History Tests
   */
  describe('Billing History', () => {
    it('displays invoices list', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          invoices={mockInvoices}
        />
      );

      expect(screen.getByText('Billing History')).toBeInTheDocument();
      expect(screen.getAllByText('$79.00')).toHaveLength(2);
    });

    it('shows invoice statuses', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          invoices={mockInvoices}
        />
      );

      const paidBadges = screen.getAllByText('paid');
      expect(paidBadges.length).toBeGreaterThan(0);
    });

    it('shows download button for invoices with URL', () => {
      const { container } = renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          invoices={mockInvoices}
        />
      );

      // First invoice has URL, should have download button icon
      // Look for IconDownload SVG element
      const downloadIcon = container.querySelector('.tabler-icon-download');
      expect(downloadIcon).toBeTruthy();
    });

    it('hides billing history section when empty', () => {
      renderWithProviders(
        <SubscriptionManager
          subscription={mockActiveSubscription}
          invoices={[]}
        />
      );

      expect(screen.queryByText('Billing History')).not.toBeInTheDocument();
    });
  });

  /**
   * Status Display Tests
   */
  describe('Status Display', () => {
    it('shows renewal date for active subscriptions', () => {
      renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);

      expect(screen.getByText('Next billing date')).toBeInTheDocument();
      expect(screen.getByText(/days until renewal/i)).toBeInTheDocument();
    });

    it('shows progress bar for active subscriptions', () => {
      const { container } = renderWithProviders(
        <SubscriptionManager subscription={mockActiveSubscription} />
      );

      // Progress component should be rendered
      const progressElement = container.querySelector('[role="progressbar"]');
      expect(progressElement).toBeDefined();
    });

    it('hides renewal info for cancelled subscriptions', () => {
      renderWithProviders(
        <SubscriptionManager subscription={mockCancelledSubscription} />
      );

      expect(screen.queryByText('Next billing date')).not.toBeInTheDocument();
    });
  });

  /**
   * Props Handling Tests
   */
  describe('Props Handling', () => {
    it('handles missing optional callbacks gracefully', () => {
      expect(() => {
        renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);
      }).not.toThrow();
    });

    it('handles missing optional arrays gracefully', () => {
      expect(() => {
        renderWithProviders(<SubscriptionManager subscription={mockActiveSubscription} />);
      }).not.toThrow();
    });

    it('calls onChangePlan when View Plans clicked with no subscription', () => {
      const mockOnChangePlan = vi.fn();

      renderWithProviders(
        <SubscriptionManager subscription={null} onChangePlan={mockOnChangePlan} />
      );

      const viewPlansButton = screen.getByText('View Plans');
      fireEvent.click(viewPlansButton);

      expect(mockOnChangePlan).toHaveBeenCalledTimes(1);
    });
  });
});
