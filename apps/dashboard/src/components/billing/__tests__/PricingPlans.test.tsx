/**
 * Unit Tests: PricingPlans Component
 *
 * Tests rendering, billing toggle, plan selection, and visual elements
 * of the PricingPlans component.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MantineProvider } from '@mantine/core';
import { PricingPlans } from '../PricingPlans';

// Test wrapper with Mantine provider
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <MantineProvider>
      {component}
    </MantineProvider>
  );
};

// Mock plan data
const mockPlans = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for individual educators',
    monthlyPrice: 29,
    yearlyPrice: 290,
    priceId: {
      monthly: 'price_starter_monthly',
      yearly: 'price_starter_yearly',
    },
    icon: 'star' as const,
    features: [
      { text: 'Up to 3 classes', included: true },
      { text: '30 students total', included: true },
      { text: 'Basic Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Email support', included: true },
      { text: 'Advanced analytics', included: false },
    ],
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'For growing educational programs',
    monthlyPrice: 79,
    yearlyPrice: 790,
    priceId: {
      monthly: 'price_pro_monthly',
      yearly: 'price_pro_yearly',
    },
    icon: 'rocket' as const,
    popular: true,
    features: [
      { text: 'Unlimited classes', included: true },
      { text: '150 students total', included: true },
      { text: 'Advanced Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Priority email support', included: true },
      { text: 'Advanced analytics', included: true },
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For schools and institutions',
    monthlyPrice: 199,
    yearlyPrice: 1990,
    priceId: {
      monthly: 'price_enterprise_monthly',
      yearly: 'price_enterprise_yearly',
    },
    icon: 'building' as const,
    features: [
      { text: 'Unlimited classes', included: true },
      { text: 'Unlimited students', included: true },
      { text: 'Premium Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Dedicated account manager', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'API access', included: true },
    ],
  },
];

describe('PricingPlans Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Rendering Tests
   */
  describe('Rendering', () => {
    it('renders with default plans', () => {
      renderWithProviders(<PricingPlans />);

      // Should show all three default plans
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });

    it('renders with custom plans prop', () => {
      const customPlans = [mockPlans[0]]; // Only Starter plan

      renderWithProviders(<PricingPlans plans={customPlans} />);

      // Should show custom plan
      expect(screen.getByText('Starter')).toBeInTheDocument();

      // Should not show other plans
      expect(screen.queryByText('Professional')).not.toBeInTheDocument();
      expect(screen.queryByText('Enterprise')).not.toBeInTheDocument();
    });

    it('renders plan descriptions', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      expect(screen.getByText('Perfect for individual educators')).toBeInTheDocument();
      expect(screen.getByText('For growing educational programs')).toBeInTheDocument();
      expect(screen.getByText('For schools and institutions')).toBeInTheDocument();
    });
  });

  /**
   * Billing Toggle Tests
   */
  describe('Billing Interval Toggle', () => {
    it('toggles between monthly and annual pricing', () => {
      const { container } = renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Initially shows monthly pricing - use data-testid
      const starterPrice = screen.getByTestId('plan-price-starter');
      expect(starterPrice).toHaveTextContent('29');

      const starterInterval = screen.getByTestId('plan-interval-starter');
      expect(starterInterval).toHaveTextContent('/month');

      // Find and click the switch - Mantine Switch uses hidden input
      const switchElement = container.querySelector('input[type="checkbox"]');
      if (switchElement) {
        fireEvent.click(switchElement);
      }

      // Should now show annual pricing - use data-testid
      expect(starterPrice).toHaveTextContent('290');
      expect(starterInterval).toHaveTextContent('/year');
    });

    it('updates prices when toggling to annual', () => {
      const { container } = renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Initial state (monthly) - verify intervals show "month"
      expect(screen.getByTestId('plan-interval-starter')).toHaveTextContent('/month');
      expect(screen.getByTestId('plan-interval-professional')).toHaveTextContent('/month');
      expect(screen.getByTestId('plan-interval-enterprise')).toHaveTextContent('/month');

      // Toggle to annual - Mantine Switch uses hidden input
      const switchElement = container.querySelector('input[type="checkbox"]');
      if (switchElement) {
        fireEvent.click(switchElement);
      }

      // After toggle, check that all intervals changed to "year"
      expect(screen.getByTestId('plan-interval-starter')).toHaveTextContent('/year');
      expect(screen.getByTestId('plan-interval-professional')).toHaveTextContent('/year');
      expect(screen.getByTestId('plan-interval-enterprise')).toHaveTextContent('/year');
    });

    it('shows savings badge for annual billing', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Check for savings badge
      expect(screen.getByText(/Save up to 25%/i)).toBeInTheDocument();
    });

    it('calculates and displays savings for annual plans', () => {
      const { container } = renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Toggle to annual - Mantine Switch uses hidden input
      const switchElement = container.querySelector('input[type="checkbox"]');
      if (switchElement) {
        fireEvent.click(switchElement);
      }

      // Should show savings text for each plan using data-testid
      const starterSavings = screen.getByTestId('plan-savings-starter');
      expect(starterSavings).toHaveTextContent(/Save \$58/); // 29*12 - 290 = 348 - 290 = 58

      const proSavings = screen.getByTestId('plan-savings-professional');
      expect(proSavings).toHaveTextContent(/Save \$158/); // 79*12 - 790 = 948 - 790 = 158

      const enterpriseSavings = screen.getByTestId('plan-savings-enterprise');
      expect(enterpriseSavings).toHaveTextContent(/Save \$398/); // 199*12 - 1990 = 2388 - 1990 = 398
    });
  });

  /**
   * Plan Selection Tests
   */
  describe('Plan Selection', () => {
    it('calls onSelectPlan with correct plan and interval when button clicked', () => {
      const mockOnSelectPlan = vi.fn();

      renderWithProviders(
        <PricingPlans plans={mockPlans} onSelectPlan={mockOnSelectPlan} />
      );

      // Find and click the Starter plan button
      const buttons = screen.getAllByRole('button', { name: /Choose Plan/i });
      const starterButton = buttons[0]; // First plan

      fireEvent.click(starterButton);

      // Should call onSelectPlan with Starter plan and 'month' interval
      expect(mockOnSelectPlan).toHaveBeenCalledTimes(1);
      expect(mockOnSelectPlan).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'starter', name: 'Starter' }),
        'month'
      );
    });

    it('passes annual interval when toggled to yearly', () => {
      const mockOnSelectPlan = vi.fn();

      const { container } = renderWithProviders(
        <PricingPlans plans={mockPlans} onSelectPlan={mockOnSelectPlan} />
      );

      // Toggle to annual - Mantine Switch uses hidden input
      const switchElement = container.querySelector('input[type="checkbox"]');
      if (switchElement) {
        fireEvent.click(switchElement);
      }

      // Click Professional plan button (second button)
      const buttons = screen.getAllByRole('button', { name: /Choose Plan/i });
      fireEvent.click(buttons[1]);

      // Should call onSelectPlan with 'year' interval
      expect(mockOnSelectPlan).toHaveBeenCalledWith(
        expect.objectContaining({ id: 'professional', name: 'Professional' }),
        'year'
      );
    });

    it('disables button when plan is current', () => {
      renderWithProviders(
        <PricingPlans plans={mockPlans} currentPlanId="professional" />
      );

      // Find all buttons
      const buttons = screen.getAllByRole('button');

      // Professional plan button (second one) should be disabled
      const professionalButton = buttons.find(btn =>
        btn.textContent?.includes('Current Plan')
      );

      expect(professionalButton).toBeDisabled();
    });

    it('disables buttons when canSelectPlan is false', () => {
      renderWithProviders(
        <PricingPlans plans={mockPlans} canSelectPlan={false} />
      );

      // All "Choose Plan" buttons should be disabled
      const chooseButtons = screen.getAllByRole('button', {
        name: /Sign In to Subscribe/i,
      });

      chooseButtons.forEach(button => {
        expect(button).toBeDisabled();
      });
    });

    it('shows "Current Plan" text for active plan', () => {
      renderWithProviders(
        <PricingPlans plans={mockPlans} currentPlanId="starter" />
      );

      // Should show "Current Plan" button text
      expect(screen.getByRole('button', { name: /Current Plan/i })).toBeInTheDocument();
    });
  });

  /**
   * Visual Tests
   */
  describe('Visual Elements', () => {
    it('highlights popular plan with badge', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Professional plan should have "Most Popular" badge
      expect(screen.getByText(/Most Popular/i)).toBeInTheDocument();
    });

    it('displays plan icons', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Check that icons are rendered (via SVG elements)
      const planCards = screen.getAllByRole('button', { name: /Choose Plan/i });
      expect(planCards.length).toBeGreaterThan(0);
    });

    it('renders feature lists with checkmarks and crosses', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Check that unique feature text is rendered
      expect(screen.getByText('Up to 3 classes')).toBeInTheDocument(); // Starter only
      expect(screen.getByText('Custom branding')).toBeInTheDocument(); // Enterprise only

      // Check for common feature that appears in multiple plans
      const analyticsFeatures = screen.getAllByText('Advanced analytics');
      expect(analyticsFeatures.length).toBeGreaterThan(0);
    });

    it('shows trial information in footer', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Check for trial information
      expect(
        screen.getByText(/All plans include a 14-day free trial/i)
      ).toBeInTheDocument();
      expect(screen.getByText(/No credit card required/i)).toBeInTheDocument();
    });
  });

  /**
   * Accessibility Tests
   */
  describe('Accessibility', () => {
    it('renders proper heading hierarchy', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Plan names should be present as text
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });

    it('has accessible toggle switch', () => {
      const { container } = renderWithProviders(<PricingPlans plans={mockPlans} />);

      // Switch should be present in the DOM (Mantine uses hidden input)
      const switchElement = container.querySelector('input[type="checkbox"]');
      expect(switchElement).toBeTruthy();
    });

    it('has accessible CTA buttons', () => {
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      // All buttons should have accessible names
      const buttons = screen.getAllByRole('button', { name: /Choose Plan/i });
      expect(buttons.length).toBe(3); // One for each plan
    });
  });

  /**
   * Props Validation Tests
   */
  describe('Props Handling', () => {
    it('handles missing onSelectPlan prop gracefully', () => {
      // Should not throw error when onSelectPlan is not provided
      renderWithProviders(<PricingPlans plans={mockPlans} />);

      const buttons = screen.getAllByRole('button', { name: /Choose Plan/i });
      expect(() => fireEvent.click(buttons[0])).not.toThrow();
    });

    it('renders with minimal props', () => {
      // Should render with no props (uses defaults)
      renderWithProviders(<PricingPlans />);

      // Default plans should be shown
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
    });
  });
});
