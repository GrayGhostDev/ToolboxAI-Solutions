/**
 * BillingPage Component
 *
 * Main billing dashboard page that integrates all billing components
 * Handles subscription management, plan selection, and payment processing
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Stack,
  Tabs,
  Card,
  Text,
  Group,
  Box,
  Badge,
  Loader,
  Alert,
  useMantineTheme
} from '@mantine/core';
import {
  IconCreditCard,
  IconReceipt,
  IconStar,
  IconAlertCircle
} from '@tabler/icons-react';
import { useAppDispatch, useAppSelector } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';
import { PricingPlans } from '../billing/PricingPlans';
import { SubscriptionManager } from '../billing/SubscriptionManager';
import { CheckoutForm } from '../billing/CheckoutForm';
import { useApiCallOnMount } from '../../hooks/useApiCall';

interface Plan {
  id: string;
  name: string;
  description: string;
  monthlyPrice: number;
  yearlyPrice: number;
  priceId: {
    monthly: string;
    yearly: string;
  };
  features: Array<{ text: string; included: boolean }>;
  popular?: boolean;
  icon: 'star' | 'rocket' | 'building';
}

export default function BillingPage() {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();
  const currentUser = useAppSelector((state) => state.user);

  // State
  const [activeTab, setActiveTab] = useState<string | null>('subscription');
  const [selectedPlan, setSelectedPlan] = useState<{
    plan: Plan;
    interval: 'month' | 'year';
  } | null>(null);
  const [showCheckout, setShowCheckout] = useState(false);

  // Fetch subscription data using API hook
  const {
    data: subscriptionData,
    loading: subscriptionLoading,
    error: subscriptionError,
    refetch: refetchSubscription
  } = useApiCallOnMount(null, {
    mockEndpoint: '/billing/subscription',
    showNotification: false
  });

  // Fetch payment methods
  const {
    data: paymentMethodsData,
    loading: paymentMethodsLoading,
    refetch: refetchPaymentMethods
  } = useApiCallOnMount(null, {
    mockEndpoint: '/billing/payment-methods',
    showNotification: false
  });

  // Fetch invoices
  const {
    data: invoicesData,
    loading: invoicesLoading,
    refetch: refetchInvoices
  } = useApiCallOnMount(null, {
    mockEndpoint: '/billing/invoices',
    showNotification: false
  });

  const subscription = subscriptionData as any;
  const paymentMethods = (paymentMethodsData as any[]) || [];
  const invoices = (invoicesData as any[]) || [];
  const loading = subscriptionLoading || paymentMethodsLoading || invoicesLoading;

  // Handle plan selection from pricing table
  const handleSelectPlan = useCallback((plan: Plan, interval: 'month' | 'year') => {
    setSelectedPlan({ plan, interval });
    setShowCheckout(true);
    setActiveTab('checkout');
  }, []);

  // Handle successful checkout
  const handleCheckoutSuccess = useCallback(async (subscriptionId: string) => {
    dispatch(
      addNotification({
        type: 'success',
        message: 'Subscription activated successfully!'
      })
    );

    // Refresh subscription data
    await refetchSubscription();
    await refetchPaymentMethods();

    // Return to subscription tab
    setShowCheckout(false);
    setSelectedPlan(null);
    setActiveTab('subscription');
  }, [dispatch, refetchSubscription, refetchPaymentMethods]);

  // Handle checkout cancellation
  const handleCheckoutCancel = useCallback(() => {
    setShowCheckout(false);
    setSelectedPlan(null);
    setActiveTab('subscription');
  }, []);

  // Handle plan change request
  const handleChangePlan = useCallback(() => {
    setActiveTab('plans');
  }, []);

  // Handle subscription cancellation
  const handleCancelSubscription = useCallback(async (subscriptionId: string) => {
    // TODO: Call backend API to cancel subscription
    await new Promise(resolve => setTimeout(resolve, 1500));

    dispatch(
      addNotification({
        type: 'success',
        message: 'Subscription cancelled successfully'
      })
    );

    // Refresh subscription data
    await refetchSubscription();
  }, [dispatch, refetchSubscription]);

  // Handle subscription reactivation
  const handleReactivateSubscription = useCallback(async (subscriptionId: string) => {
    // TODO: Call backend API to reactivate subscription
    await new Promise(resolve => setTimeout(resolve, 1500));

    dispatch(
      addNotification({
        type: 'success',
        message: 'Subscription reactivated successfully'
      })
    );

    // Refresh subscription data
    await refetchSubscription();
  }, [dispatch, refetchSubscription]);

  if (loading && !subscription) {
    return (
      <Container size="lg" style={{ padding: theme.spacing.xl }}>
        <Stack gap="xl" align="center" style={{ minHeight: 400, justifyContent: 'center' }}>
          <Loader size="lg" />
          <Text c="dimmed">Loading billing information...</Text>
        </Stack>
      </Container>
    );
  }

  return (
    <Container size="xl" style={{ padding: theme.spacing.xl }}>
      <Stack gap="xl">
        {/* Page Header */}
        <Box>
          <Group justify="space-between" align="flex-start">
            <Box>
              <Text size="32px" fw={700} mb="xs">
                Billing & Subscription
              </Text>
              <Text size="md" c="dimmed">
                Manage your subscription, payment methods, and billing history
              </Text>
            </Box>
            {subscription && (
              <Badge
                size="xl"
                color={subscription.status === 'active' ? 'green' : 'yellow'}
                leftSection={<IconStar size={14} />}
              >
                {subscription.planName}
              </Badge>
            )}
          </Group>
        </Box>

        {/* Error Alert */}
        {subscriptionError && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="red"
            title="Error loading subscription"
          >
            {subscriptionError}
          </Alert>
        )}

        {/* Checkout Mode */}
        {showCheckout && selectedPlan ? (
          <Box>
            <Card shadow="sm" padding="md" radius="md" withBorder mb="lg">
              <Group justify="space-between">
                <Text size="lg" fw={600}>
                  Complete Your Purchase
                </Text>
                <Text size="sm" c="dimmed">
                  Step 2 of 2
                </Text>
              </Group>
            </Card>

            <CheckoutForm
              priceId={
                selectedPlan.interval === 'month'
                  ? selectedPlan.plan.priceId.monthly
                  : selectedPlan.plan.priceId.yearly
              }
              planName={selectedPlan.plan.name}
              planPrice={
                selectedPlan.interval === 'month'
                  ? `$${selectedPlan.plan.monthlyPrice}`
                  : `$${selectedPlan.plan.yearlyPrice}`
              }
              interval={selectedPlan.interval}
              onSuccess={handleCheckoutSuccess}
              onCancel={handleCheckoutCancel}
            />
          </Box>
        ) : (
          /* Tabs Navigation */
          <Tabs value={activeTab} onChange={setActiveTab}>
            <Tabs.List>
              <Tabs.Tab value="subscription" leftSection={<IconCreditCard size={16} />}>
                Subscription
              </Tabs.Tab>
              <Tabs.Tab value="plans" leftSection={<IconStar size={16} />}>
                Plans & Pricing
              </Tabs.Tab>
              <Tabs.Tab value="invoices" leftSection={<IconReceipt size={16} />}>
                Invoices
              </Tabs.Tab>
            </Tabs.List>

            {/* Subscription Tab */}
            <Tabs.Panel value="subscription" pt="xl">
              <SubscriptionManager
                subscription={subscription}
                paymentMethods={paymentMethods}
                invoices={invoices.slice(0, 5)} // Show only recent invoices
                onChangePlan={handleChangePlan}
                onCancelSubscription={handleCancelSubscription}
                onReactivateSubscription={handleReactivateSubscription}
              />
            </Tabs.Panel>

            {/* Plans Tab */}
            <Tabs.Panel value="plans" pt="xl">
              <PricingPlans
                currentPlanId={subscription?.planId}
                onSelectPlan={handleSelectPlan}
                canSelectPlan={true}
              />
            </Tabs.Panel>

            {/* Invoices Tab */}
            <Tabs.Panel value="invoices" pt="xl">
              <Card shadow="md" padding="lg" radius="md" withBorder>
                <Stack gap="md">
                  <Text size="lg" fw={700}>
                    All Invoices
                  </Text>

                  {invoices.length === 0 ? (
                    <Box style={{ textAlign: 'center', padding: theme.spacing.xl }}>
                      <Text size="lg" c="dimmed" mb="xs">
                        No invoices yet
                      </Text>
                      <Text size="sm" c="dimmed">
                        Your billing history will appear here once you have an active subscription
                      </Text>
                    </Box>
                  ) : (
                    <Stack gap="xs">
                      {invoices.map((invoice: any) => (
                        <Box
                          key={invoice.id}
                          style={{
                            padding: theme.spacing.md,
                            borderRadius: theme.radius.md,
                            border: `1px solid ${theme.colors.gray[3]}`,
                            backgroundColor: theme.white
                          }}
                        >
                          <Group justify="space-between">
                            <Box>
                              <Text size="sm" fw={500}>
                                {new Date(invoice.date).toLocaleDateString('en-US', {
                                  year: 'numeric',
                                  month: 'long',
                                  day: 'numeric'
                                })}
                              </Text>
                              <Text size="xs" c="dimmed">
                                Invoice #{invoice.id.slice(-12)}
                              </Text>
                            </Box>
                            <Group gap="md">
                              <Text size="sm" fw={600}>
                                {invoice.amount}
                              </Text>
                              <Badge
                                size="sm"
                                color={
                                  invoice.status === 'paid'
                                    ? 'green'
                                    : invoice.status === 'pending'
                                    ? 'yellow'
                                    : 'red'
                                }
                              >
                                {invoice.status.toUpperCase()}
                              </Badge>
                            </Group>
                          </Group>
                        </Box>
                      ))}
                    </Stack>
                  )}
                </Stack>
              </Card>
            </Tabs.Panel>
          </Tabs>
        )}
      </Stack>
    </Container>
  );
}
