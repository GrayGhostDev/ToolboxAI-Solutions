/**
 * Unit Tests: BillingPage Component
 *
 * Tests page rendering, tab navigation, checkout flow, and component integration
 * of the BillingPage component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import BillingPage from '../BillingPage';
import uiSlice from '../../../store/slices/uiSlice';
import userSlice from '../../../store/slices/userSlice';
import * as useApiCall from '../../../hooks/useApiCall';

// Mock child components
vi.mock('../../billing/PricingPlans', () => ({
  PricingPlans: ({ onSelectPlan }: any) => (
    <div data-testid="pricing-plans">
      <button onClick={() => onSelectPlan({ id: 'starter', name: 'Starter', priceId: { monthly: 'pm_1', yearly: 'py_1' }, monthlyPrice: 29, yearlyPrice: 290 }, 'month')}>
        Select Plan
      </button>
    </div>
  ),
}));

vi.mock('../../billing/SubscriptionManager', () => ({
  SubscriptionManager: ({ onChangePlan, onCancelSubscription }: any) => (
    <div data-testid="subscription-manager">
      <button onClick={onChangePlan}>Change Plan</button>
      <button onClick={() => onCancelSubscription('sub_123')}>Cancel</button>
    </div>
  ),
}));

vi.mock('../../billing/CheckoutForm', () => ({
  CheckoutForm: ({ onSuccess, onCancel }: any) => (
    <div data-testid="checkout-form">
      <button onClick={() => onSuccess('sub_new')}>Complete</button>
      <button onClick={onCancel}>Cancel Checkout</button>
    </div>
  ),
}));

// Test wrapper with required providers
const renderWithProviders = (component: React.ReactElement) => {
  const mockStore = configureStore({
    reducer: {
      ui: uiSlice,
      user: userSlice,
    },
    preloadedState: {
      user: {
        id: 1,
        email: 'test@example.com',
        role: 'teacher',
      },
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
const mockSubscription = {
  id: 'sub_123',
  planId: 'professional',
  planName: 'Professional',
  planPrice: '$79',
  interval: 'month' as const,
  status: 'active' as const,
  currentPeriodEnd: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
  cancelAtPeriodEnd: false,
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
];

const mockInvoices = [
  {
    id: 'in_123',
    date: new Date().toISOString(),
    amount: '$79.00',
    status: 'paid' as const,
  },
];

describe('BillingPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Page Rendering Tests
   */
  describe('Rendering', () => {
    it('shows loading state while fetching data', () => {
      // Mock useApiCallOnMount to return loading state
      vi.spyOn(useApiCall, 'useApiCallOnMount').mockReturnValue({
        data: null,
        loading: true,
        error: null,
        refetch: vi.fn(),
      } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByText('Loading billing information...')).toBeInTheDocument();
    });

    it('renders page header with title', () => {
      // Mock successful data fetch
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByText('Billing & Subscription')).toBeInTheDocument();
      expect(
        screen.getByText(/Manage your subscription, payment methods, and billing history/i)
      ).toBeInTheDocument();
    });

    it('shows error alert when subscription fetch fails', () => {
      // Mock error state
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: null,
          loading: false,
          error: 'Failed to load subscription',
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: [],
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: [],
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByText('Error loading subscription')).toBeInTheDocument();
      expect(screen.getByText('Failed to load subscription')).toBeInTheDocument();
    });

    it('renders all tabs', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByRole('tab', { name: /Subscription/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Plans & Pricing/i })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: /Invoices/i })).toBeInTheDocument();
    });
  });

  /**
   * Tab Navigation Tests
   */
  describe('Tab Navigation', () => {
    it('defaults to subscription tab', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByTestId('subscription-manager')).toBeInTheDocument();
    });

    it('switches to plans tab when clicked', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      const plansTab = screen.getByRole('tab', { name: /Plans & Pricing/i });
      fireEvent.click(plansTab);

      expect(screen.getByTestId('pricing-plans')).toBeInTheDocument();
    });

    it('switches to invoices tab when clicked', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: [],
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      const invoicesTab = screen.getByRole('tab', { name: /Invoices/i });
      fireEvent.click(invoicesTab);

      expect(screen.getByText('All Invoices')).toBeInTheDocument();
    });
  });

  /**
   * Integration Tests
   */
  describe('Integration', () => {
    it('navigates to checkout when plan selected', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Navigate to plans tab
      const plansTab = screen.getByRole('tab', { name: /Plans & Pricing/i });
      fireEvent.click(plansTab);

      // Select a plan
      const selectButton = screen.getByText('Select Plan');
      fireEvent.click(selectButton);

      // Should show checkout form
      expect(screen.getByTestId('checkout-form')).toBeInTheDocument();
      expect(screen.getByText('Complete Your Purchase')).toBeInTheDocument();
    });

    it('returns to subscription tab after checkout success', async () => {
      const mockRefetch = vi.fn();
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: mockRefetch,
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: mockRefetch,
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Navigate to plans and select
      fireEvent.click(screen.getByRole('tab', { name: /Plans & Pricing/i }));
      fireEvent.click(screen.getByText('Select Plan'));

      // Complete checkout
      const completeButton = screen.getByText('Complete');
      fireEvent.click(completeButton);

      // Should return to subscription tab
      await waitFor(() => {
        expect(screen.getByTestId('subscription-manager')).toBeInTheDocument();
      });

      // Should refetch subscription data
      expect(mockRefetch).toHaveBeenCalled();
    });

    it('returns to subscription tab when checkout cancelled', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Navigate to plans and select
      fireEvent.click(screen.getByRole('tab', { name: /Plans & Pricing/i }));
      fireEvent.click(screen.getByText('Select Plan'));

      // Cancel checkout
      const cancelButton = screen.getByText('Cancel Checkout');
      fireEvent.click(cancelButton);

      // Should return to subscription tab
      expect(screen.getByTestId('subscription-manager')).toBeInTheDocument();
    });

    it('navigates to plans tab when change plan clicked from subscription manager', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Click change plan from subscription manager
      const changePlanButton = screen.getByText('Change Plan');
      fireEvent.click(changePlanButton);

      // Should show pricing plans
      expect(screen.getByTestId('pricing-plans')).toBeInTheDocument();
    });

    it('refetches subscription after cancellation', async () => {
      const mockRefetch = vi.fn();
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: mockRefetch,
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Click cancel from subscription manager
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);

      // Should refetch after cancellation
      await waitFor(() => {
        expect(mockRefetch).toHaveBeenCalled();
      });
    });
  });

  /**
   * Props Handling Tests
   */
  describe('Props Handling', () => {
    it('handles empty invoices list', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: [],
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: [],
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      // Navigate to invoices tab
      fireEvent.click(screen.getByRole('tab', { name: /Invoices/i }));

      expect(screen.getByText('No invoices yet')).toBeInTheDocument();
    });

    it('displays current plan badge in header', () => {
      vi.spyOn(useApiCall, 'useApiCallOnMount')
        .mockReturnValueOnce({
          data: mockSubscription,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockPaymentMethods,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any)
        .mockReturnValueOnce({
          data: mockInvoices,
          loading: false,
          error: null,
          refetch: vi.fn(),
        } as any);

      renderWithProviders(<BillingPage />);

      expect(screen.getByText('Professional')).toBeInTheDocument();
    });
  });
});
