import { Overlay, Stack, Loader, Text, Box } from '@mantine/core';
import { Roblox3DLoader } from '../roblox/Roblox3DLoader';
import { useMantineTheme } from '@mantine/core';

interface Props {
  message?: string;
  use3DLoader?: boolean;
}

export function LoadingOverlay({ message = 'Loading awesome stuff...', use3DLoader = true }: Props) {
  const theme = useMantineTheme();

  return (
    <Overlay
      opacity={0.95}
      blur={5}
      color="rgba(15, 15, 46, 0.95)"
      zIndex={1000}
    >
      <Box
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          color: 'white',
        }}
      >
        {use3DLoader ? (
          <Roblox3DLoader
            message={message}
            variant="both"
            size="large"
            showBackground={true}
          />
        ) : (
          <Stack align="center" spacing="md">
            <Loader color="cyan" size="xl" variant="dots" />
            <Text size="lg" fw={600}>
              {message}
            </Text>
          </Stack>
        )}
      </Box>
    </Overlay>
  );
}