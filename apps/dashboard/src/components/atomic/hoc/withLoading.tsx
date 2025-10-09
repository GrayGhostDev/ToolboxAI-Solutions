/**
 * withLoading HOC
 *
 * Wraps components with loading state management and loading UI.
 * Provides consistent loading behavior across the application.
 */

import React from 'react';
import { AtomicBox, AtomicSpinner, AtomicText } from '../atoms';

export interface WithLoadingProps {
  loading?: boolean;
  loadingText?: string;
  loadingComponent?: React.ComponentType<LoadingComponentProps>;
  spinnerSize?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  spinnerVariant?: 'circular' | 'dots' | 'pulse' | 'bars';
  overlay?: boolean;
  minHeight?: string | number;
}

export interface LoadingComponentProps {
  loading?: boolean;
  loadingText?: string;
  spinnerSize?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  spinnerVariant?: 'circular' | 'dots' | 'pulse' | 'bars';
}

// Default loading component
const DefaultLoadingComponent: React.FunctionComponent<LoadingComponentProps> = ({
  loadingText = 'Loading...',
  spinnerSize = 'md',
  spinnerVariant = 'circular'
}) => (
  <AtomicBox
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    p={6}
    gap={3}
  >
    <AtomicSpinner
      size={spinnerSize}
      variant={spinnerVariant}
      robloxTheme={true}
    />
    {loadingText && (
      <AtomicText
        variant="sm"
        color="gray"
        textAlign="center"
      >
        {loadingText}
      </AtomicText>
    )}
  </AtomicBox>
);

// Overlay loading component
const OverlayLoadingComponent: React.FunctionComponent<LoadingComponentProps> = ({
  loadingText = 'Loading...',
  spinnerSize = 'lg',
  spinnerVariant = 'circular'
}) => (
  <AtomicBox
    position="absolute"
    top={0}
    left={0}
    right={0}
    bottom={0}
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    bg="rgba(255, 255, 255, 0.8)"
    backdropFilter="blur(4px)"
    zIndex={1000}
  >
    <AtomicSpinner
      size={spinnerSize}
      variant={spinnerVariant}
      robloxTheme={true}
    />
    {loadingText && (
      <AtomicText
        variant="base"
        color="blue"
        textAlign="center"
        mt={2}
        weight="medium"
      >
        {loadingText}
      </AtomicText>
    )}
  </AtomicBox>
);

/**
 * HOC that adds loading state management to a component
 *
 * @param WrappedComponent - Component to wrap with loading functionality
 * @param defaultOptions - Default loading configuration options
 * @returns Enhanced component with loading state
 *
 * @example
 * const LoadingCard = withLoading(Card, {
 *   loadingText: 'Loading card data...',
 *   spinnerSize: 'md',
 *   overlay: false
 * });
 *
 * // Usage
 * <LoadingCard loading={isLoading} title="My Card">
 *   Card content
 * </LoadingCard>
 */
const withLoading = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  defaultOptions: WithLoadingProps = {}
) => {
  const ComponentWithLoading = ({ ...props, ref }) => {
      const {
        loading = false,
        loadingText,
        loadingComponent: LoadingComponent,
        spinnerSize = 'md',
        spinnerVariant = 'circular',
        overlay = false,
        minHeight,
        ...wrappedProps
      } = { ...defaultOptions, ...props };

      // Choose the appropriate loading component
      const FinalLoadingComponent = LoadingComponent ||
        (overlay ? OverlayLoadingComponent : DefaultLoadingComponent);

      // If not loading, render the wrapped component normally
      if (!loading) {
        return <WrappedComponent {...(wrappedProps as P)} ref={ref} />;
      }

      // If overlay loading, render component with overlay
      if (overlay) {
        return (
          <AtomicBox position="relative" minHeight={minHeight}>
            <WrappedComponent {...(wrappedProps as P)} ref={ref} />
            <FinalLoadingComponent
              loading={loading}
              loadingText={loadingText}
              spinnerSize={spinnerSize}
              spinnerVariant={spinnerVariant}
            />
          </AtomicBox>
        );
      }

      // Regular loading (replace component)
      return (
        <AtomicBox minHeight={minHeight}>
          <FinalLoadingComponent
            loading={loading}
            loadingText={loadingText}
            spinnerSize={spinnerSize}
            spinnerVariant={spinnerVariant}
          />
        </AtomicBox>
      );
    };


  ComponentWithLoading.displayName = `withLoading(${
    WrappedComponent.displayName || WrappedComponent.name || 'Component'
  })`;

  return ComponentWithLoading;
};

// Utility function to create loading HOC with preset options
const createLoadingHOC = (options: WithLoadingProps) => {
  return <P extends object>(WrappedComponent: React.ComponentType<P>) =>
    withLoading(WrappedComponent, options);
};

// Preset loading HOCs for common patterns
export const withOverlayLoading = createLoadingHOC({
  overlay: true,
  loadingText: 'Loading...',
  spinnerSize: 'lg'
});

export const withCardLoading = createLoadingHOC({
  overlay: false,
  loadingText: 'Loading content...',
  spinnerSize: 'md',
  minHeight: 200
});

export const withPageLoading = createLoadingHOC({
  overlay: false,
  loadingText: 'Loading page...',
  spinnerSize: 'lg',
  minHeight: '50vh'
});

export const withButtonLoading = createLoadingHOC({
  overlay: true,
  loadingText: '',
  spinnerSize: 'sm'
});

export type { WithLoadingProps, LoadingComponentProps };
export default withLoading;