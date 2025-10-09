/**
 * CheckoutForm Component
 *
 * Stripe Elements checkout form for processing subscription payments
 * Handles credit card input, validation, and payment submission
 */

import React, { useState, useCallback } from 'react';
import {
  Card,
  Stack,
  Button,
  Text,
  Alert,
  Loader,
  Group,
  Box,
  useMantineTheme
} from '@mantine/core';
import {
  IconCreditCard,
  IconLock,
  IconAlertCircle
} from '@tabler/icons-react';
import { useAppDispatch } from '../../store';
import { addNotification } from '../../store/slices/uiSlice';

interface CheckoutFormProps {
  /** Price ID for the selected plan */
  priceId: string;
  /** Plan name for display */
  planName: string;
  /** Plan price for display */
  planPrice: string;
  /** Billing interval (monthly/yearly) */
  interval: 'month' | 'year';
  /** Callback on successful payment */
  onSuccess?: (subscriptionId: string) => void;
  /** Callback on payment cancellation */
  onCancel?: () => void;
}

export function CheckoutForm({
  priceId,
  planName,
  planPrice,
  interval,
  onSuccess,
  onCancel
}: CheckoutFormProps) {
  const theme = useMantineTheme();
  const dispatch = useAppDispatch();

  // State
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cardholderName, setCardholderName] = useState('');
  const [cardComplete, setCardComplete] = useState(false);

  // Handle form submission
  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();

    if (!cardComplete) {
      setError('Please enter complete card details');
      return;
    }

    if (!cardholderName.trim()) {
      setError('Please enter cardholder name');
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      // TODO: Integrate with Stripe.js
      // 1. Create payment method
      // 2. Attach to customer
      // 3. Create subscription

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));

      dispatch(
        addNotification({
          type: 'success',
          message: `Successfully subscribed to ${planName} plan!`
        })
      );

      // Call success callback with mock subscription ID
      onSuccess?.('sub_mock_' + Date.now());
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Payment failed';
      setError(errorMessage);

      dispatch(
        addNotification({
          type: 'error',
          message: `Payment failed: ${errorMessage}`
        })
      );
    } finally {
      setProcessing(false);
    }
  }, [cardComplete, cardholderName, planName, dispatch, onSuccess]);

  return (
    <Card shadow="md" padding="xl" radius="md" withBorder>
      <form onSubmit={handleSubmit}>
        <Stack gap="lg">
          {/* Header */}
          <Box>
            <Text size="xl" fw={700} mb="xs">
              Complete Your Subscription
            </Text>
            <Text size="sm" c="dimmed">
              Subscribe to {planName} - {planPrice}/{interval}
            </Text>
          </Box>

          {/* Error Alert */}
          {error && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              color="red"
              title="Payment Error"
              withCloseButton
              onClose={() => setError(null)}
            >
              {error}
            </Alert>
          )}

          {/* Cardholder Name */}
          <Box>
            <Text size="sm" fw={500} mb="xs">
              Cardholder Name
            </Text>
            <input
              type="text"
              value={cardholderName}
              onChange={(e) => setCardholderName(e.target.value)}
              placeholder="John Doe"
              disabled={processing}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: theme.radius.md,
                border: `1px solid ${theme.colors.gray[4]}`,
                fontSize: '14px',
                fontFamily: theme.fontFamily
              }}
            />
          </Box>

          {/* Card Element Placeholder */}
          <Box>
            <Text size="sm" fw={500} mb="xs">
              Card Information
            </Text>
            <Box
              style={{
                padding: '12px',
                borderRadius: theme.radius.md,
                border: `1px solid ${theme.colors.gray[4]}`,
                backgroundColor: theme.colors.gray[0],
                minHeight: '44px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <Group gap="xs">
                <IconCreditCard size={20} color={theme.colors.gray[6]} />
                <Text size="sm" c="dimmed">
                  Stripe Card Element will be mounted here
                </Text>
              </Group>
            </Box>
            <Text size="xs" c="dimmed" mt="xs">
              Your payment information is encrypted and secure
            </Text>
          </Box>

          {/* Security Notice */}
          <Box
            style={{
              padding: theme.spacing.md,
              borderRadius: theme.radius.md,
              backgroundColor: theme.colors.blue[0],
              border: `1px solid ${theme.colors.blue[2]}`
            }}
          >
            <Group gap="xs">
              <IconLock size={16} color={theme.colors.blue[6]} />
              <Text size="xs" c={theme.colors.blue[7]}>
                Your payment is secured by Stripe. We never see or store your card details.
              </Text>
            </Group>
          </Box>

          {/* Order Summary */}
          <Box
            style={{
              padding: theme.spacing.md,
              borderRadius: theme.radius.md,
              backgroundColor: theme.colors.gray[0],
              border: `1px solid ${theme.colors.gray[3]}`
            }}
          >
            <Stack gap="xs">
              <Group justify="space-between">
                <Text size="sm" fw={500}>
                  {planName} Plan
                </Text>
                <Text size="sm" fw={500}>
                  {planPrice}
                </Text>
              </Group>
              <Group justify="space-between">
                <Text size="xs" c="dimmed">
                  Billing {interval === 'month' ? 'Monthly' : 'Annually'}
                </Text>
                <Text size="xs" c="dimmed">
                  per {interval}
                </Text>
              </Group>
              <Box
                style={{
                  height: '1px',
                  backgroundColor: theme.colors.gray[3],
                  margin: `${theme.spacing.xs} 0`
                }}
              />
              <Group justify="space-between">
                <Text size="md" fw={700}>
                  Total Today
                </Text>
                <Text size="md" fw={700} c={theme.colors.blue[6]}>
                  {planPrice}
                </Text>
              </Group>
            </Stack>
          </Box>

          {/* Action Buttons */}
          <Group justify="space-between" mt="md">
            <Button
              variant="subtle"
              onClick={onCancel}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={processing || !cardComplete || !cardholderName.trim()}
              leftSection={processing ? <Loader size="xs" color="white" /> : <IconLock size={16} />}
            >
              {processing ? 'Processing...' : `Subscribe for ${planPrice}`}
            </Button>
          </Group>
        </Stack>
      </form>
    </Card>
  );
}

export default CheckoutForm;
