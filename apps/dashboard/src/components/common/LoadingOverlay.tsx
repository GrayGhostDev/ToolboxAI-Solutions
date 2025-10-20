import { Overlay, Stack, Loader, Text, Box } from '@mantine/core';
// Roblox3DLoader temporarily disabled for Vercel build
// import { Roblox3DLoader } from '../roblox/Roblox3DLoader';

interface Props {
  message?: string;
  // use3DLoader temporarily disabled
  // use3DLoader?: boolean;
}

export function LoadingOverlay({ message = 'Loading awesome stuff...' }: Props) {
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
        {/* Roblox3DLoader temporarily disabled - using standard loader */}
        <Stack align="center" gap="md">
          <Loader color="cyan" size="xl" variant="dots" />
          <Text size="lg" fw={600}>
            {message}
          </Text>
        </Stack>
      </Box>
    </Overlay>
  );
}