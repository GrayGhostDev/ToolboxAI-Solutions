import { Button, ButtonProps, Loader } from '@mantine/core';
import { IconCheck } from '@tabler/icons-react';
import { ReactNode } from 'react';

interface LoadingButtonProps extends Omit<ButtonProps, 'leftSection'> {
  loading?: boolean;
  success?: boolean;
  successMessage?: string;
  icon?: ReactNode;
  leftSection?: ReactNode;
}

/**
 * LoadingButton - Enhanced button with loading and success states
 * 
 * @example
 * <LoadingButton 
 *   loading={isSubmitting} 
 *   success={submitSuccess}
 *   successMessage="Saved!"
 *   onClick={handleSubmit}
 *   leftSection={<IconSave size={16} />}
 * >
 *   Save Changes
 * </LoadingButton>
 */
export function LoadingButton({
  loading = false,
  success = false,
  successMessage,
  icon,
  children,
  leftSection,
  disabled,
  ...props
}: LoadingButtonProps) {
  const renderLeftSection = () => {
    if (loading) return <Loader size={16} />;
    if (success) return <IconCheck size={16} />;
    return leftSection || icon;
  };

  return (
    <Button
      {...props}
      disabled={loading || success || disabled}
      leftSection={renderLeftSection()}
    >
      {success && successMessage ? successMessage : children}
    </Button>
  );
}
