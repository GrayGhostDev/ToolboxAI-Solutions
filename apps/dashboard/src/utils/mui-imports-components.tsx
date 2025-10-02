/**
 * Mantine Component Wrappers - JSX components that wrap Mantine with MUI-compatible props
 * This file provides wrapper components for complex MUI sub-components
 */

import React from 'react';
import { Accordion, Menu, Radio, Tabs, Button, Group, Pagination, Anchor } from '@mantine/core';

// Proper Mantine-compatible component wrappers for complex MUI sub-components
export const CardContent: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ padding: '1rem', ...style }}>{children}</div>
);

export const CardActions: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ padding: '0.5rem 1rem', display: 'flex', gap: '0.5rem', ...style }}>{children}</div>
);

export const CardMedia: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={style}>{children}</div>
);

export const CardHeader: React.FC<{ children?: React.ReactNode; title?: string; style?: React.CSSProperties }> = ({
  children,
  title,
  style
}) => (
  <div style={{ padding: '1rem', fontWeight: 600, ...style }}>
    {title || children}
  </div>
);

export const ListItem: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties; onClick?: () => void }> = ({
  children,
  style,
  onClick
}) => (
  <li style={{ listStyle: 'none', padding: '0.5rem', cursor: onClick ? 'pointer' : 'default', ...style }} onClick={onClick}>
    {children}
  </li>
);

export const ListItemText: React.FC<{
  primary?: React.ReactNode;
  secondary?: React.ReactNode;
  style?: React.CSSProperties
}> = ({ primary, secondary, style }) => (
  <span style={style}>
    {primary && <div style={{ fontWeight: 500 }}>{primary}</div>}
    {secondary && <div style={{ fontSize: '0.875rem', color: '#666' }}>{secondary}</div>}
  </span>
);

export const ListItemAvatar: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div style={{ marginRight: '1rem', display: 'flex', alignItems: 'center' }}>{children}</div>
);

export const ListItemIcon: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div style={{ marginRight: '1rem', display: 'flex', alignItems: 'center', minWidth: '40px' }}>{children}</div>
);

export const ListItemButton: React.FC<{ children?: React.ReactNode; onClick?: () => void }> = ({ children, onClick }) => (
  <div
    style={{ padding: '0.5rem', cursor: 'pointer', borderRadius: '4px' }}
    onClick={onClick}
  >
    {children}
  </div>
);

export const DialogTitle: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, ...style }}>{children}</h2>
);

export const DialogContent: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ padding: '1rem 0', ...style }}>{children}</div>
);

export const DialogActions: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', paddingTop: '1rem', ...style }}>
    {children}
  </div>
);

export const DialogContentText: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <p style={{ margin: '0.5rem 0', color: '#666', ...style }}>{children}</p>
);

export const FormControl: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties; size?: 'small' | 'medium' }> = ({
  children,
  style
}) => (
  <div style={{ marginBottom: '1rem', ...style }}>{children}</div>
);

export const InputLabel: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <label style={{ display: 'block', marginBottom: '0.25rem', fontSize: '0.875rem', fontWeight: 500, ...style }}>
    {children}
  </label>
);

export const InputAdornment: React.FC<{ children?: React.ReactNode; position?: 'start' | 'end' }> = ({ children }) => (
  <div style={{ display: 'flex', alignItems: 'center' }}>{children}</div>
);

export const FormControlLabel: React.FC<{
  control: React.ReactElement;
  label: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ control, label, style }) => (
  <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', ...style }}>
    {control}
    <span>{label}</span>
  </label>
);

export const TableBody: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <tbody>{children}</tbody>
);

export const TableCell: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <td style={{ padding: '0.75rem', ...style }}>{children}</td>
);

export const TableContainer: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ overflowX: 'auto', ...style }}>{children}</div>
);

export const TableHead: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <thead>{children}</thead>
);

export const TableRow: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <tr style={style}>{children}</tr>
);

export const TablePagination: React.FC<{
  count: number;
  page: number;
  rowsPerPage: number;
  onPageChange: (event: any, page: number) => void;
  onRowsPerPageChange?: (event: any) => void;
}> = ({ count, page, rowsPerPage, onPageChange }) => (
  <div style={{ padding: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
    <Pagination
      total={Math.ceil(count / rowsPerPage)}
      value={page + 1}
      onChange={(p) => onPageChange(null, p - 1)}
    />
  </div>
);

export const AppBar: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties; position?: string }> = ({
  children,
  style
}) => (
  <header style={{ padding: '1rem', ...style }}>{children}</header>
);

export const Toolbar: React.FC<{ children?: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', ...style }}>{children}</div>
);

export const MenuItem: React.FC<{
  children?: React.ReactNode;
  value?: any;
  onClick?: () => void;
  style?: React.CSSProperties;
}> = ({ children, onClick, style }) => (
  <Menu.Item onClick={onClick} style={style}>
    {children}
  </Menu.Item>
);

export const RadioGroup: React.FC<{ children?: React.ReactNode; value?: any; onChange?: (e: any) => void }> = ({
  children,
  value,
  onChange
}) => (
  <Radio.Group value={value} onChange={onChange}>
    {children}
  </Radio.Group>
);

export const Tab: React.FC<{ label?: string; icon?: React.ReactNode; iconPosition?: 'start' | 'end' }> = ({
  label,
  icon
}) => (
  <Tabs.Tab value={label || ''} leftSection={icon}>
    {label}
  </Tabs.Tab>
);

export const AlertTitle: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>{children}</div>
);

export const ToggleButton: React.FC<{ children?: React.ReactNode; value?: any; selected?: boolean }> = ({ children }) => (
  <Button variant="default">{children}</Button>
);

export const ToggleButtonGroup: React.FC<{ children?: React.ReactNode; value?: any; onChange?: (e: any, value: any) => void }> = ({
  children
}) => (
  <Group>{children}</Group>
);

// Additional Mantine component wrappers
export const AccordionSummary: React.FC<{ children?: React.ReactNode; expandIcon?: React.ReactNode }> = ({ children, expandIcon }) => (
  <Accordion.Control icon={expandIcon}>{children}</Accordion.Control>
);

export const AccordionDetails: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <Accordion.Panel>{children}</Accordion.Panel>
);

export const ListItemSecondaryAction: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>{children}</div>
);

// Link component wrapper
export const Link: React.FC<{
  children?: React.ReactNode;
  href?: string;
  onClick?: () => void;
  style?: React.CSSProperties;
  underline?: 'none' | 'hover' | 'always';
}> = ({ children, href, onClick, style, underline = 'hover' }) => (
  <Anchor href={href} onClick={onClick} style={style} underline={underline}>
    {children}
  </Anchor>
);

// CacheProvider stub (not needed in Mantine)
export const CacheProvider: React.FC<{ children?: React.ReactNode; value?: any }> = ({ children }) => (
  <>{children}</>
);

