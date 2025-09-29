/**
 * Table Compound Component
 *
 * A flexible table component using compound component pattern.
 * Provides context-based composition for maximum flexibility.
 */

import React, { createContext, useContext, forwardRef } from 'react';
import { Table as MantineTable, TableProps as MantineTableProps, Box } from '@mantine/core';
import { AtomicText } from '../atoms';
import { designTokens } from '../../../theme/designTokens';

// Table Context
interface TableContextValue {
  sortable?: boolean;
  selectable?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'striped' | 'bordered' | 'roblox';
  robloxTheme?: boolean;
}

const TableContext = createContext<TableContextValue>({});

const useTableContext = () => {
  const context = useContext(TableContext);
  return context;
};

// Table Component Props
export interface TableProps {
  children: React.ReactNode;
  sortable?: boolean;
  selectable?: boolean;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'striped' | 'bordered' | 'roblox';
  robloxTheme?: boolean;
}

// Table Root Component
const TableRoot = forwardRef<HTMLTableElement, TableProps>(
  (
    {
      children,
      sortable = false,
      selectable = false,
      size = 'md',
      variant = 'default',
      robloxTheme = true,
      ...props
    },
    ref
  ) => {
    const contextValue: TableContextValue = {
      sortable,
      selectable,
      size,
      variant,
      robloxTheme
    };

    // Get Mantine size
    const getMantineSize = () => {
      switch (size) {
        case 'sm': return 'sm';
        case 'lg': return 'lg';
        default: return 'md';
      }
    };

    // Get table styles based on variant
    const getTableStyles = () => {
      const baseStyles = {
        fontSize: designTokens.typography.fontSize.sm[0],
      };

      switch (variant) {
        case 'striped':
          return {
            ...baseStyles,
            '& tbody tr:nth-of-type(even) td': {
              backgroundColor: 'var(--mantine-color-gray-1)'
            }
          };

        case 'bordered':
          return {
            ...baseStyles,
            border: '1px solid var(--mantine-color-gray-4)',
            '& th, & td': {
              border: '1px solid var(--mantine-color-gray-4)'
            }
          };

        case 'roblox':
          return {
            ...baseStyles,
            border: `2px solid ${robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)'}`,
            borderRadius: designTokens.borderRadius.lg,
            overflow: 'hidden',
            '& thead th': {
              backgroundColor: robloxTheme ? 'rgba(226, 35, 26, 0.1)' : 'var(--mantine-color-blue-1)',
              borderBottom: `2px solid ${robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)'}`
            }
          };

        default:
          return baseStyles;
      }
    };

    // Generate CSS for special variants
    const getSpecialCSS = () => {
      if (variant === 'roblox') {
        return `
          .roblox-table {
            overflow: hidden;
          }
          .roblox-table thead th {
            background-color: ${robloxTheme ? 'rgba(226, 35, 26, 0.1)' : 'var(--mantine-color-blue-1)'};
            border-bottom: 2px solid ${robloxTheme ? '#E2231A' : 'var(--mantine-color-blue-6)'};
          }
        `;
      }
      return '';
    };

    return (
      <TableContext.Provider value={contextValue}>
        {variant === 'roblox' && (
          <style dangerouslySetInnerHTML={{ __html: getSpecialCSS() }} />
        )}

        <Box
          style={{
            width: '100%',
            overflowX: 'auto',
            borderRadius: designTokens.borderRadius.lg,
            ...(variant !== 'roblox' && variant !== 'bordered' && {
              border: '1px solid var(--mantine-color-gray-4)'
            })
          }}
        >
          <MantineTable
            ref={ref}
            size={getMantineSize()}
            striped={variant === 'striped'}
            withTableBorder={variant === 'bordered'}
            withColumnBorders={variant === 'bordered'}
            style={getTableStyles()}
            className={variant === 'roblox' ? 'roblox-table' : undefined}
            {...props}
          >
            {children}
          </MantineTable>
        </Box>
      </TableContext.Provider>
    );
  }
);

// Table Header Component
interface TableHeaderProps {
  children: React.ReactNode;
}

const TableHeader = forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ children, ...props }, ref) => {
    return (
      <MantineTable.Thead ref={ref} {...props}>
        {children}
      </MantineTable.Thead>
    );
  }
);

// Table Body Component
interface TableBodyProps {
  children: React.ReactNode;
}

const TableBody = forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ children, ...props }, ref) => {
    return (
      <MantineTable.Tbody ref={ref} {...props}>
        {children}
      </MantineTable.Tbody>
    );
  }
);

// Table Row Component
interface TableRowProps {
  children: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
}

const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ children, selected = false, onClick, ...props }, ref) => {
    const { selectable } = useTableContext();

    const getRowStyles = () => {
      const baseStyles: React.CSSProperties = {
        transition: `background-color ${designTokens.animation.duration.fast} ${designTokens.animation.easing.inOut}`,
      };

      if (selectable) {
        baseStyles.cursor = 'pointer';
      }

      if (selected) {
        baseStyles.backgroundColor = 'var(--mantine-color-blue-1)';
      }

      return baseStyles;
    };

    const getHoverStyles = () => {
      if (!selectable) return {};

      return {
        '&:hover': {
          backgroundColor: 'var(--mantine-color-gray-1)'
        }
      };
    };

    return (
      <MantineTable.Tr
        ref={ref}
        style={getRowStyles()}
        styles={{
          root: getHoverStyles()
        }}
        onClick={onClick}
        {...props}
      >
        {children}
      </MantineTable.Tr>
    );
  }
);

// Table Cell Component
interface TableCellProps {
  children: React.ReactNode;
  as?: 'td' | 'th';
  sortable?: boolean;
  sorted?: 'asc' | 'desc' | false;
  onSort?: () => void;
  align?: 'left' | 'center' | 'right';
  width?: string | number;
}

const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  (
    {
      children,
      as: Component = 'td',
      sortable = false,
      sorted = false,
      onSort,
      align = 'left',
      width,
      ...props
    },
    ref
  ) => {
    const { sortable: tableSortable } = useTableContext();
    const isSortable = sortable && tableSortable;

    const handleSort = () => {
      if (isSortable && onSort) {
        onSort();
      }
    };

    const getCellStyles = () => {
      const baseStyles: React.CSSProperties = {
        textAlign: align,
        cursor: isSortable ? 'pointer' : 'default'
      };

      if (width) {
        baseStyles.width = typeof width === 'number' ? `${width}px` : width;
      }

      return baseStyles;
    };

    const CellComponent = Component === 'th' ? MantineTable.Th : MantineTable.Td;

    return (
      <CellComponent
        ref={ref}
        style={getCellStyles()}
        onClick={isSortable ? handleSort : undefined}
        {...props}
      >
        {isSortable ? (
          <Box
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start'
            }}
          >
            {children}
            {sorted && (
              <AtomicText variant="xs" style={{ marginLeft: '4px' }}>
                {sorted === 'asc' ? '↑' : '↓'}
              </AtomicText>
            )}
          </Box>
        ) : (
          children
        )}
      </CellComponent>
    );
  }
);

// Compound component export
const Table = Object.assign(TableRoot, {
  Header: TableHeader,
  Body: TableBody,
  Row: TableRow,
  Cell: TableCell
});

Table.displayName = 'Table';
TableHeader.displayName = 'Table.Header';
TableBody.displayName = 'Table.Body';
TableRow.displayName = 'Table.Row';
TableCell.displayName = 'Table.Cell';

export type { TableProps };
export default Table;