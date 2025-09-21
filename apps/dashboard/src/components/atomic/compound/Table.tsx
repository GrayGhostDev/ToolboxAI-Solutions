/**
 * Table Compound Component
 *
 * A flexible table component using compound component pattern.
 * Provides context-based composition for maximum flexibility.
 */

import React, { createContext, useContext, forwardRef } from 'react';
import { styled } from '@mui/material/styles';
import { AtomicBox, AtomicText, AtomicCheckbox } from '../atoms';
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

// Styled Components
const StyledTable = styled('table')<TableContextValue>(({
  theme,
  size = 'md',
  variant = 'default',
  robloxTheme = true
}) => {
  const sizeMap = {
    sm: { padding: designTokens.spacing[1.5] },
    md: { padding: designTokens.spacing[2] },
    lg: { padding: designTokens.spacing[3] }
  };

  const baseStyles = {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: designTokens.typography.fontSize.sm[0],

    '& th, & td': {
      padding: sizeMap[size].padding,
      textAlign: 'left' as const,
      borderBottom: `1px solid ${theme.palette.divider}`
    },

    '& th': {
      fontWeight: designTokens.typography.fontWeight.semibold,
      color: theme.palette.text.primary,
      backgroundColor: theme.palette.background.default
    }
  };

  switch (variant) {
    case 'striped':
      return {
        ...baseStyles,
        '& tbody tr:nth-of-type(even)': {
          backgroundColor: theme.palette.action.hover
        }
      };

    case 'bordered':
      return {
        ...baseStyles,
        border: `1px solid ${theme.palette.divider}`,

        '& th, & td': {
          ...baseStyles['& th, & td'],
          border: `1px solid ${theme.palette.divider}`
        }
      };

    case 'roblox':
      return {
        ...baseStyles,
        border: `2px solid ${robloxTheme ? '#E2231A' : theme.palette.primary.main}`,
        borderRadius: designTokens.borderRadius.lg,
        overflow: 'hidden',

        '& th': {
          ...baseStyles['& th'],
          backgroundColor: robloxTheme ? 'rgba(226, 35, 26, 0.1)' : theme.palette.primary.light,
          borderBottom: `2px solid ${robloxTheme ? '#E2231A' : theme.palette.primary.main}`
        }
      };

    default:
      return baseStyles;
  }
});

const StyledTableContainer = styled(AtomicBox)(({ theme }) => ({
  width: '100%',
  overflowX: 'auto',
  borderRadius: designTokens.borderRadius.lg,
  border: `1px solid ${theme.palette.divider}`
}));

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

    return (
      <TableContext.Provider value={contextValue}>
        <StyledTableContainer>
          <StyledTable
            ref={ref}
            size={size}
            variant={variant}
            robloxTheme={robloxTheme}
            {...props}
          >
            {children}
          </StyledTable>
        </StyledTableContainer>
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
      <thead ref={ref} {...props}>
        {children}
      </thead>
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
      <tbody ref={ref} {...props}>
        {children}
      </tbody>
    );
  }
);

// Table Row Component
interface TableRowProps {
  children: React.ReactNode;
  selected?: boolean;
  onClick?: () => void;
}

const StyledTableRow = styled('tr')<{ selectable?: boolean; selected?: boolean }>(({
  theme,
  selectable,
  selected
}) => ({
  transition: `background-color ${designTokens.animation.duration.fast} ${designTokens.animation.easing.inOut}`,

  ...(selectable && {
    cursor: 'pointer',

    '&:hover': {
      backgroundColor: theme.palette.action.hover
    }
  }),

  ...(selected && {
    backgroundColor: theme.palette.action.selected
  })
}));

const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ children, selected = false, onClick, ...props }, ref) => {
    const { selectable } = useTableContext();

    return (
      <StyledTableRow
        ref={ref}
        selectable={selectable}
        selected={selected}
        onClick={(e: React.MouseEvent) => onClick}
        {...props}
      >
        {children}
      </StyledTableRow>
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

const StyledTableCell = styled('td')<TableCellProps>(({
  align = 'left',
  width
}) => ({
  textAlign: align,
  ...(width && {
    width: typeof width === 'number' ? `${width}px` : width
  })
}));

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

    return (
      <StyledTableCell
        ref={ref}
        as={Component}
        align={align}
        width={width}
        onClick={(e: React.MouseEvent) => isSortable ? handleSort : undefined}
        style={{
          cursor: isSortable ? 'pointer' : 'default'
        }}
        {...props}
      >
        {isSortable ? (
          <AtomicBox
            display="flex"
            alignItems="center"
            justifyContent={align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start'}
          >
            {children}
            {sorted && (
              <AtomicText variant="xs" style={{ marginLeft: '4px' }}>
                {sorted === 'asc' ? '↑' : '↓'}
              </AtomicText>
            )}
          </AtomicBox>
        ) : (
          children
        )}
      </StyledTableCell>
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