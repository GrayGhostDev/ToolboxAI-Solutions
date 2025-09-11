# UserActivityChart

## Component Information

- **Category**: analytics
- **Type**: functional
- **File**: `src/dashboard/src/components/analytics/UserActivityChart.tsx`

## Props

| Prop        | Type      | Required | Description |
| ----------- | --------- | -------- | ----------- | ------ | --- | --- |
| timeRange   | `"24h"    | "7d"     | "30d"       | "90d"` | ❌  |     |
| height      | `number`  | ❌       |             |
| autoRefresh | `boolean` | ❌       |             |

## Hooks Used

- `useTheme`
- `useWebSocketContext`
- `useState`
- `useCallback`
- `useEffect`

## State Management

- Local component state
- WebSocket connections

## Key Dependencies

- `@mui/material/styles`
- `react`
