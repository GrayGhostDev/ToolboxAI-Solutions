/**
 * SubscriptionManager Component
 *
 * Manages user's active subscription including upgrades, downgrades, and cancellations
 * Shows current plan details, billing history, and payment methods
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  Stack,
  Button,
  Text,
  Badge,
  Group,
  Box,
  Divider,
  Modal,
  Alert,
  Progress,
  ActionIcon,
  Tooltip,
  useMantineTheme
} from '@mantine/core';
import {
  IconCheck,
  IconX,
  IconCreditCard,
  IconAlertCircle,
  IconTrendingUp,
  IconTrendingDown,
  IconRefresh,
  IconDownload,
  IconEdit
} from '@tabler/icons-react';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';

interface Subscription {
  id: string;
  planName: string;
  planPrice: string;
  interval: 'month' | 'year';
  status: 'active' | 'cancelled' | 'past_due' | 'trialing';
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
  trialEnd?: string;
}

interface PaymentMethod {
  id: string;
  brand: string;
  last4: string;
  expMonth: number;
  expYear: number;
  isDefault: boolean;
}

interface Invoice {
  id: string;
  date: string;
  amount: string;
  status: 'paid' | 'pending' | 'failed';
  invoiceUrl?: string;
}

interface SubscriptionManagerProps {
  /** Current subscription data */
  subscription: Subscription | null;
  /** Payment methods */
  paymentMethods?: PaymentMethod[];
  /** Recent invoices */
  invoices?: Invoice[];
  /** Callback for plan changes */
  onChangePlan?: () => void;
  /** Callback for cancellation */
  onCancelSubscription?: (subscriptionId: string) => void;
  /** Callback for reactivation */
  onReactivateSubscription?: (subscriptionId: string) => void;
}

export function SubscriptionManager({
  subscription,
  paymentMethods = [],
  invoices = [],
  onChangePlan,
  onCancelSubscription,
  onReactivateSubscription
}: SubscriptionManagerProps) {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();

  // State
  const [cancelModalOpen, setCancelModalOpen] = useState(false);
  const [processing, setProcessing] = useState(false);

  // Get subscription status color
  const getStatusColor = (status: Subscription['status']) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'trialing':
        return 'blue';
      case 'cancelled':
        return 'gray';
      case 'past_due':
        return 'red';
      default:
        return 'gray';
    }
  };

  // Handle subscription cancellation
  const handleCancelSubscription = useCallback(async () => {
    if (!subscription) return;

    setProcessing(true);
    try {
      // TODO: Integrate with backend API
      await new Promise(resolve => setTimeout(resolve, 1500));

      onCancelSubscription?.(subscription.id);

      dispatch(
        addNotification({
          type: 'success',
          message: 'Subscription cancelled successfully. You will retain access until the end of your billing period.'
        })
      );

      setCancelModalOpen(false);
    } catch (err) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to cancel subscription. Please try again.'
        })
      );
    } finally {
      setProcessing(false);
    }
  }, [subscription, onCancelSubscription, dispatch]);

  // Handle subscription reactivation
  const handleReactivateSubscription = useCallback(async () => {
    if (!subscription) return;

    setProcessing(true);
    try {
      // TODO: Integrate with backend API
      await new Promise(resolve => setTimeout(resolve, 1500));

      onReactivateSubscription?.(subscription.id);

      dispatch(
        addNotification({
          type: 'success',
          message: 'Subscription reactivated successfully!'
        })
      );
    } catch (err) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Failed to reactivate subscription. Please try again.'
        })
      );
    } finally {
      setProcessing(false);
    }
  }, [subscription, onReactivateSubscription, dispatch]);

  // Handle invoice download
  const handleDownloadInvoice = useCallback((invoice: Invoice) => {
    if (invoice.invoiceUrl) {
      window.open(invoice.invoiceUrl, '_blank');
    } else {
      dispatch(
        addNotification({
          type: 'info',
          message: 'Invoice download link not available'
        })
      );
    }
  }, [dispatch]);

  if (!subscription) {
    return (
      <Card shadow="md" padding="xl" radius="md" withBorder>
        <Stack gap="md" align="center" style={{ textAlign: 'center', padding: theme.spacing.xl }}>
          <IconAlertCircle size={48} color={theme.colors.gray[5]} />
          <Text size="lg" fw={600} c="dimmed">
            No Active Subscription
          </Text>
          <Text size="sm" c="dimmed" style={{ maxWidth: 400 }}>
            You don't have an active subscription. Choose a plan to get started with premium features.
          </Text>
          <Button onClick={onChangePlan} leftSection={<IconTrendingUp size={16} />}>
            View Plans
          </Button>
        </Stack>
      </Card>
    );
  }

  const daysUntilRenewal = Math.ceil(
    (new Date(subscription.currentPeriodEnd).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
  );

  return (
    <Stack gap="lg">
      {/* Current Plan Card */}
      <Card shadow="md" padding="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group justify="space-between" align="flex-start">
            <Box>
              <Group gap="xs" mb="xs">
                <Text size="xl" fw={700}>
                  {subscription.planName}
                </Text>
                <Badge color={getStatusColor(subscription.status)} size="lg">
                  {subscription.status.toUpperCase()}
                </Badge>
              </Group>
              <Text size="lg" c={theme.colors.blue[6]} fw={600}>
                {subscription.planPrice}/{subscription.interval}
              </Text>
            </Box>
            <Group gap="xs">
              <Button
                variant="outline"
                leftSection={<IconRefresh size={16} />}
                onClick={onChangePlan}
              >
                Change Plan
              </Button>
            </Group>
          </Group>

          <Divider />

          {/* Subscription Status */}
          <Stack gap="sm">
            {subscription.status === 'trialing' && subscription.trialEnd && (
              <Alert color="blue" icon={<IconCheck size={16} />}>
                Your trial ends on {new Date(subscription.trialEnd).toLocaleDateString()}.
                You will be automatically charged {subscription.planPrice} on that date.
              </Alert>
            )}

            {subscription.cancelAtPeriodEnd && (
              <Alert color="yellow" icon={<IconAlertCircle size={16} />}>
                Your subscription is scheduled to cancel on {new Date(subscription.currentPeriodEnd).toLocaleDateString()}.
                You will retain access until then.
              </Alert>
            )}

            {subscription.status === 'past_due' && (
              <Alert color="red" icon={<IconX size={16} />}>
                Your payment is past due. Please update your payment method to continue your subscription.
              </Alert>
            )}

            {subscription.status === 'active' && !subscription.cancelAtPeriodEnd && (
              <Box>
                <Group justify="space-between" mb="xs">
                  <Text size="sm" fw={500}>
                    Next billing date
                  </Text>
                  <Text size="sm" fw={600}>
                    {new Date(subscription.currentPeriodEnd).toLocaleDateString()}
                  </Text>
                </Group>
                <Progress value={(30 - daysUntilRenewal) / 30 * 100} size="sm" color="blue" />
                <Text size="xs" c="dimmed" mt="xs">
                  {daysUntilRenewal} days until renewal
                </Text>
              </Box>
            )}
          </Stack>

          {/* Action Buttons */}
          <Group mt="md">
            {subscription.cancelAtPeriodEnd ? (
              <Button
                variant="filled"
                color="green"
                leftSection={<IconCheck size={16} />}
                onClick={handleReactivateSubscription}
                disabled={processing}
              >
                Reactivate Subscription
              </Button>
            ) : (
              <Button
                variant="subtle"
                color="red"
                leftSection={<IconX size={16} />}
                onClick={() => setCancelModalOpen(true)}
                disabled={processing}
              >
                Cancel Subscription
              </Button>
            )}
          </Group>
        </Stack>
      </Card>

      {/* Payment Methods Card */}
      {paymentMethods.length > 0 && (
        <Card shadow="md" padding="lg" radius="md" withBorder>
          <Stack gap="md">
            <Group justify="space-between">
              <Text size="lg" fw={700}>
                Payment Methods
              </Text>
              <Button variant="outline" size="xs" leftSection={<IconEdit size={14} />}>
                Manage
              </Button>
            </Group>

            <Stack gap="xs">
              {paymentMethods.map((method) => (
                <Box
                  key={method.id}
                  style={{
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    border: `1px solid ${theme.colors.gray[3]}`,
                    backgroundColor: method.isDefault ? theme.colors.blue[0] : theme.white
                  }}
                >
                  <Group justify="space-between">
                    <Group gap="md">
                      <IconCreditCard size={24} color={theme.colors.gray[7]} />
                      <Box>
                        <Text size="sm" fw={500}>
                          {method.brand.toUpperCase()} •••• {method.last4}
                        </Text>
                        <Text size="xs" c="dimmed">
                          Expires {method.expMonth}/{method.expYear}
                        </Text>
                      </Box>
                    </Group>
                    {method.isDefault && (
                      <Badge size="sm" color="blue">
                        Default
                      </Badge>
                    )}
                  </Group>
                </Box>
              ))}
            </Stack>
          </Stack>
        </Card>
      )}

      {/* Billing History Card */}
      {invoices.length > 0 && (
        <Card shadow="md" padding="lg" radius="md" withBorder>
          <Stack gap="md">
            <Text size="lg" fw={700}>
              Billing History
            </Text>

            <Stack gap="xs">
              {invoices.map((invoice) => (
                <Box
                  key={invoice.id}
                  style={{
                    padding: theme.spacing.md,
                    borderRadius: theme.radius.md,
                    border: `1px solid ${theme.colors.gray[3]}`
                  }}
                >
                  <Group justify="space-between">
                    <Box>
                      <Text size="sm" fw={500}>
                        {new Date(invoice.date).toLocaleDateString()}
                      </Text>
                      <Text size="xs" c="dimmed">
                        Invoice #{invoice.id.slice(-8)}
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
                        {invoice.status}
                      </Badge>
                      {invoice.invoiceUrl && (
                        <Tooltip label="Download Invoice">
                          <ActionIcon
                            variant="subtle"
                            size="sm"
                            onClick={() => handleDownloadInvoice(invoice)}
                          >
                            <IconDownload size={16} />
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </Group>
                  </Group>
                </Box>
              ))}
            </Stack>
          </Stack>
        </Card>
      )}

      {/* Cancellation Modal */}
      <Modal
        opened={cancelModalOpen}
        onClose={() => setCancelModalOpen(false)}
        title="Cancel Subscription"
        size="md"
      >
        <Stack gap="md">
          <Alert color="yellow" icon={<IconAlertCircle size={16} />}>
            Are you sure you want to cancel your subscription? You will lose access to premium features
            at the end of your billing period on {new Date(subscription.currentPeriodEnd).toLocaleDateString()}.
          </Alert>

          <Text size="sm">
            If you're having issues with your subscription, please contact our support team before cancelling.
          </Text>

          <Group justify="flex-end" mt="md">
            <Button
              variant="subtle"
              onClick={() => setCancelModalOpen(false)}
              disabled={processing}
            >
              Keep Subscription
            </Button>
            <Button
              color="red"
              onClick={handleCancelSubscription}
              disabled={processing}
              leftSection={<IconX size={16} />}
            >
              {processing ? 'Cancelling...' : 'Confirm Cancellation'}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}

export default SubscriptionManager;
