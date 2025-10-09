/**
 * PricingPlans Component
 *
 * Displays available subscription plans with features and pricing
 * Supports monthly/annual toggle and plan selection
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
  SimpleGrid,
  Switch,
  List,
  ThemeIcon,
  useMantineTheme
} from '@mantine/core';
import {
  IconCheck,
  IconStar,
  IconRocket,
  IconBuilding,
  IconSparkles
} from '@tabler/icons-react';

interface PlanFeature {
  text: string;
  included: boolean;
}

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
  features: PlanFeature[];
  popular?: boolean;
  icon: 'star' | 'rocket' | 'building';
}

interface PricingPlansProps {
  /** Available plans */
  plans?: Plan[];
  /** Currently active plan ID */
  currentPlanId?: string;
  /** Callback when plan is selected */
  onSelectPlan?: (plan: Plan, interval: 'month' | 'year') => void;
  /** Whether user can select plans (authenticated) */
  canSelectPlan?: boolean;
}

// Default plans configuration
const DEFAULT_PLANS: Plan[] = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for individual educators',
    monthlyPrice: 29,
    yearlyPrice: 290,
    priceId: {
      monthly: 'price_starter_monthly',
      yearly: 'price_starter_yearly'
    },
    icon: 'star',
    features: [
      { text: 'Up to 3 classes', included: true },
      { text: '30 students total', included: true },
      { text: 'Basic Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Email support', included: true },
      { text: 'Advanced analytics', included: false },
      { text: 'Custom branding', included: false },
      { text: 'API access', included: false }
    ]
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'For growing educational programs',
    monthlyPrice: 79,
    yearlyPrice: 790,
    priceId: {
      monthly: 'price_pro_monthly',
      yearly: 'price_pro_yearly'
    },
    icon: 'rocket',
    popular: true,
    features: [
      { text: 'Unlimited classes', included: true },
      { text: '150 students total', included: true },
      { text: 'Advanced Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Priority email support', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'API access', included: false }
    ]
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'For schools and institutions',
    monthlyPrice: 199,
    yearlyPrice: 1990,
    priceId: {
      monthly: 'price_enterprise_monthly',
      yearly: 'price_enterprise_yearly'
    },
    icon: 'building',
    features: [
      { text: 'Unlimited classes', included: true },
      { text: 'Unlimited students', included: true },
      { text: 'Premium Roblox environments', included: true },
      { text: 'AI-powered content generation', included: true },
      { text: 'Dedicated account manager', included: true },
      { text: 'Advanced analytics', included: true },
      { text: 'Custom branding', included: true },
      { text: 'API access', included: true }
    ]
  }
];

export function PricingPlans({
  plans = DEFAULT_PLANS,
  currentPlanId,
  onSelectPlan,
  canSelectPlan = true
}: PricingPlansProps) {
  const theme = useMantineTheme();
  const [isYearly, setIsYearly] = useState(false);

  // Get plan icon
  const getPlanIcon = (icon: Plan['icon']) => {
    const iconProps = { size: 32 };
    switch (icon) {
      case 'star':
        return <IconStar {...iconProps} />;
      case 'rocket':
        return <IconRocket {...iconProps} />;
      case 'building':
        return <IconBuilding {...iconProps} />;
      default:
        return <IconStar {...iconProps} />;
    }
  };

  // Calculate savings for annual billing
  const calculateSavings = (monthlyPrice: number, yearlyPrice: number) => {
    const monthlyCost = monthlyPrice * 12;
    const savings = monthlyCost - yearlyPrice;
    const savingsPercent = Math.round((savings / monthlyCost) * 100);
    return { amount: savings, percent: savingsPercent };
  };

  return (
    <Stack gap="xl">
      {/* Billing Toggle */}
      <Box style={{ textAlign: 'center' }}>
        <Group justify="center" gap="md" mb="md">
          <Text size="lg" fw={isYearly ? 400 : 700} c={isYearly ? 'dimmed' : 'dark'}>
            Monthly
          </Text>
          <Switch
            size="lg"
            checked={isYearly}
            onChange={(event) => setIsYearly(event.currentTarget.checked)}
            styles={{
              track: {
                cursor: 'pointer'
              }
            }}
          />
          <Group gap="xs">
            <Text size="lg" fw={isYearly ? 700 : 400} c={isYearly ? 'dark' : 'dimmed'}>
              Annual
            </Text>
            <Badge color="green" size="sm" variant="filled">
              Save up to 25%
            </Badge>
          </Group>
        </Group>
      </Box>

      {/* Plans Grid */}
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
        {plans.map((plan) => {
          const price = isYearly ? plan.yearlyPrice : plan.monthlyPrice;
          const priceId = isYearly ? plan.priceId.yearly : plan.priceId.monthly;
          const isCurrentPlan = currentPlanId === plan.id;
          const savings = calculateSavings(plan.monthlyPrice, plan.yearlyPrice);

          return (
            <Card
              key={plan.id}
              shadow="md"
              padding="xl"
              radius="md"
              withBorder
              style={{
                position: 'relative',
                borderColor: plan.popular ? theme.colors.blue[5] : theme.colors.gray[3],
                borderWidth: plan.popular ? 2 : 1,
                transform: plan.popular ? 'scale(1.05)' : 'none',
                zIndex: plan.popular ? 1 : 0
              }}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <Badge
                  color="blue"
                  size="lg"
                  variant="filled"
                  leftSection={<IconSparkles size={14} />}
                  style={{
                    position: 'absolute',
                    top: -12,
                    left: '50%',
                    transform: 'translateX(-50%)'
                  }}
                >
                  Most Popular
                </Badge>
              )}

              <Stack gap="md">
                {/* Plan Header */}
                <Box style={{ textAlign: 'center' }}>
                  <ThemeIcon
                    size={64}
                    radius="md"
                    variant="light"
                    color={plan.popular ? 'blue' : 'gray'}
                    mb="md"
                  >
                    {getPlanIcon(plan.icon)}
                  </ThemeIcon>
                  <Text size="xl" fw={700} mb="xs">
                    {plan.name}
                  </Text>
                  <Text size="sm" c="dimmed" mb="lg">
                    {plan.description}
                  </Text>
                </Box>

                {/* Pricing */}
                <Box style={{ textAlign: 'center' }}>
                  <Group justify="center" align="baseline" gap={4} data-testid={`plan-price-${plan.id}`}>
                    <Text size="sm" c="dimmed">
                      $
                    </Text>
                    <Text size={48} fw={900} lh={1}>
                      {price}
                    </Text>
                    <Text size="sm" c="dimmed" data-testid={`plan-interval-${plan.id}`}>
                      /{isYearly ? 'year' : 'month'}
                    </Text>
                  </Group>

                  {isYearly && (
                    <Text size="xs" c="green" fw={600} mt="xs" data-testid={`plan-savings-${plan.id}`}>
                      Save ${savings.amount} ({savings.percent}% off)
                    </Text>
                  )}
                </Box>

                {/* Features List */}
                <List
                  spacing="sm"
                  size="sm"
                  icon={
                    <ThemeIcon color="green" size={20} radius="xl">
                      <IconCheck size={12} />
                    </ThemeIcon>
                  }
                  style={{ marginTop: theme.spacing.md }}
                >
                  {plan.features.map((feature, index) => (
                    <List.Item
                      key={index}
                      icon={
                        feature.included ? (
                          <ThemeIcon color="green" size={20} radius="xl">
                            <IconCheck size={12} />
                          </ThemeIcon>
                        ) : (
                          <ThemeIcon color="gray" size={20} radius="xl" variant="light">
                            <Text size="xs" fw={700}>
                              —
                            </Text>
                          </ThemeIcon>
                        )
                      }
                      style={{
                        color: feature.included ? theme.black : theme.colors.gray[5],
                        textDecoration: feature.included ? 'none' : 'none'
                      }}
                    >
                      {feature.text}
                    </List.Item>
                  ))}
                </List>

                {/* CTA Button */}
                <Button
                  fullWidth
                  size="lg"
                  variant={plan.popular ? 'filled' : 'outline'}
                  color={plan.popular ? 'blue' : 'gray'}
                  disabled={isCurrentPlan || !canSelectPlan}
                  onClick={() => onSelectPlan?.(plan, isYearly ? 'year' : 'month')}
                  mt="md"
                >
                  {isCurrentPlan
                    ? 'Current Plan'
                    : canSelectPlan
                    ? 'Choose Plan'
                    : 'Sign In to Subscribe'}
                </Button>
              </Stack>
            </Card>
          );
        })}
      </SimpleGrid>

      {/* Additional Info */}
      <Box style={{ textAlign: 'center', marginTop: theme.spacing.xl }}>
        <Text size="sm" c="dimmed">
          All plans include a 14-day free trial. No credit card required. Cancel anytime.
        </Text>
      </Box>
    </Stack>
  );
}

export default PricingPlans;
