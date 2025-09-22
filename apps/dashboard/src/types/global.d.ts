// Global type definitions for ToolBoxAI Dashboard

import * as React from 'react';

// Fix Material-UI component typing issues
declare module '@mui/material/Alert' {
  import { AlertProps } from '@mui/material';
  const Alert: React.ComponentType<AlertProps>;
  export default Alert;
}

declare module '@mui/material/Button' {
  import { ButtonProps } from '@mui/material';
  const Button: React.ComponentType<ButtonProps>;
  export default Button;
}

declare module '@mui/material/Chip' {
  import { ChipProps } from '@mui/material';
  const Chip: React.ComponentType<ChipProps>;
  export default Chip;
}

declare module '@mui/material/IconButton' {
  import { IconButtonProps } from '@mui/material';
  const IconButton: React.ComponentType<IconButtonProps>;
  export default IconButton;
}

declare module '@mui/material/Box' {
  import { BoxProps } from '@mui/material';
  const Box: React.ComponentType<BoxProps>;
  export default Box;
}

declare module '@mui/material/Typography' {
  import { TypographyProps } from '@mui/material';
  const Typography: React.ComponentType<TypographyProps>;
  export default Typography;
}

declare module '@mui/material/Card' {
  import { CardProps } from '@mui/material';
  const Card: React.ComponentType<CardProps>;
  export default Card;
}

declare module '@mui/material/CardContent' {
  import { CardContentProps } from '@mui/material';
  const CardContent: React.ComponentType<CardContentProps>;
  export default CardContent;
}

declare module '@mui/material/CardHeader' {
  import { CardHeaderProps } from '@mui/material';
  const CardHeader: React.ComponentType<CardHeaderProps>;
  export default CardHeader;
}

declare module '@mui/material/Grid' {
  import { GridProps } from '@mui/material';
  const Grid: React.ComponentType<GridProps>;
  export default Grid;
}

declare module '@mui/material/Container' {
  import { ContainerProps } from '@mui/material';
  const Container: React.ComponentType<ContainerProps>;
  export default Container;
}

declare module '@mui/material/Stack' {
  import { StackProps } from '@mui/material';
  const Stack: React.ComponentType<StackProps>;
  export default Stack;
}

declare module '@mui/material/TextField' {
  import { TextFieldProps } from '@mui/material';
  const TextField: React.ComponentType<TextFieldProps>;
  export default TextField;
}

declare module '@mui/material/Select' {
  import { SelectProps } from '@mui/material';
  const Select: React.ComponentType<SelectProps>;
  export default Select;
}

declare module '@mui/material/MenuItem' {
  import { MenuItemProps } from '@mui/material';
  const MenuItem: React.ComponentType<MenuItemProps>;
  export default MenuItem;
}

declare module '@mui/material/FormControl' {
  import { FormControlProps } from '@mui/material';
  const FormControl: React.ComponentType<FormControlProps>;
  export default FormControl;
}

declare module '@mui/material/InputLabel' {
  import { InputLabelProps } from '@mui/material';
  const InputLabel: React.ComponentType<InputLabelProps>;
  export default InputLabel;
}

declare module '@mui/material/Tab' {
  import { TabProps } from '@mui/material';
  const Tab: React.ComponentType<TabProps>;
  export default Tab;
}

declare module '@mui/material/Tabs' {
  import { TabsProps } from '@mui/material';
  const Tabs: React.ComponentType<TabsProps>;
  export default Tabs;
}

declare module '@mui/material/Paper' {
  import { PaperProps } from '@mui/material';
  const Paper: React.ComponentType<PaperProps>;
  export default Paper;
}

declare module '@mui/material/Checkbox' {
  import { CheckboxProps } from '@mui/material';
  const Checkbox: React.ComponentType<CheckboxProps>;
  export default Checkbox;
}

declare module '@mui/material/Switch' {
  import { SwitchProps } from '@mui/material';
  const Switch: React.ComponentType<SwitchProps>;
  export default Switch;
}

declare module '@mui/material/Dialog' {
  import { DialogProps } from '@mui/material';
  const Dialog: React.ComponentType<DialogProps>;
  export default Dialog;
}

declare module '@mui/material/DialogTitle' {
  import { DialogTitleProps } from '@mui/material';
  const DialogTitle: React.ComponentType<DialogTitleProps>;
  export default DialogTitle;
}

declare module '@mui/material/DialogContent' {
  import { DialogContentProps } from '@mui/material';
  const DialogContent: React.ComponentType<DialogContentProps>;
  export default DialogContent;
}

declare module '@mui/material/DialogActions' {
  import { DialogActionsProps } from '@mui/material';
  const DialogActions: React.ComponentType<DialogActionsProps>;
  export default DialogActions;
}

declare module '@mui/material/CircularProgress' {
  import { CircularProgressProps } from '@mui/material';
  const CircularProgress: React.ComponentType<CircularProgressProps>;
  export default CircularProgress;
}

declare module '@mui/material/LinearProgress' {
  import { LinearProgressProps } from '@mui/material';
  const LinearProgress: React.ComponentType<LinearProgressProps>;
  export default LinearProgress;
}

declare module '@mui/material/Table' {
  import { TableProps } from '@mui/material';
  const Table: React.ComponentType<TableProps>;
  export default Table;
}

declare module '@mui/material/TableBody' {
  import { TableBodyProps } from '@mui/material';
  const TableBody: React.ComponentType<TableBodyProps>;
  export default TableBody;
}

declare module '@mui/material/TableCell' {
  import { TableCellProps } from '@mui/material';
  const TableCell: React.ComponentType<TableCellProps>;
  export default TableCell;
}

declare module '@mui/material/TableContainer' {
  import { TableContainerProps } from '@mui/material';
  const TableContainer: React.ComponentType<TableContainerProps>;
  export default TableContainer;
}

declare module '@mui/material/TableHead' {
  import { TableHeadProps } from '@mui/material';
  const TableHead: React.ComponentType<TableHeadProps>;
  export default TableHead;
}

declare module '@mui/material/TableRow' {
  import { TableRowProps } from '@mui/material';
  const TableRow: React.ComponentType<TableRowProps>;
  export default TableRow;
}

// Window interface extensions
declare global {
  interface Window {
    __REDUX_DEVTOOLS_EXTENSION__?: any;
    __TOOLBOXAI_CONFIG__?: {
      apiUrl: string;
      wsUrl: string;
      version: string;
    };
  }
}

// Environment variables
declare namespace NodeJS {
  interface ProcessEnv {
    NODE_ENV: 'development' | 'production' | 'test';
    VITE_API_BASE_URL?: string;
    VITE_WS_URL?: string;
    VITE_ENABLE_WEBSOCKET?: string;
    VITE_PUSHER_KEY?: string;
    VITE_PUSHER_CLUSTER?: string;
    VITE_PUSHER_AUTH_ENDPOINT?: string;
  }
}

export {};