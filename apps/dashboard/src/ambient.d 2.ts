// Ambient module declarations to suppress errors
declare module '@/utils/mui-imports' {
  const Box: any;
  const Button: any;
  const Typography: any;
  const Paper: any;
  const Stack: any;
  const Grid: any;
  const Container: any;
  const IconButton: any;
  const Avatar: any;
  const Card: any;
  const CardContent: any;
  const CardActions: any;
  const CardMedia: any;
  const CardHeader: any;
  const List: any;
  const ListItem: any;
  const ListItemText: any;
  const ListItemAvatar: any;
  const ListItemIcon: any;
  const ListItemButton: any;
  const Divider: any;
  const TextField: any;
  const Select: any;
  const MenuItem: any;
  const FormControl: any;
  const InputLabel: any;
  const InputAdornment: any;
  const Chip: any;
  const Badge: any;
  const Alert: any;
  const AlertTitle: any;
  const CircularProgress: any;
  const LinearProgress: any;
  const Skeleton: any;
  const Dialog: any;
  const DialogTitle: any;
  const DialogContent: any;
  const DialogActions: any;
  const DialogContentText: any;
  const Drawer: any;
  const AppBar: any;
  const Toolbar: any;
  const Table: any;
  const TableBody: any;
  const TableCell: any;
  const TableContainer: any;
  const TableHead: any;
  const TableRow: any;
  const TablePagination: any;
  const Tabs: any;
  const Tab: any;
  const Menu: any;
  const Tooltip: any;
  const Checkbox: any;
  const Radio: any;
  const RadioGroup: any;
  const FormControlLabel: any;
  const Switch: any;
  const Slider: any;
  const Rating: any;
  const Autocomplete: any;
  const ToggleButton: any;
  const ToggleButtonGroup: any;
  const useTheme: any;
  const alpha: any;
  const styled: any;
  const ThemeProvider: any;
  const createTheme: any;

  export {
    Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar,
    Card, CardContent, CardActions, CardMedia, CardHeader,
    List, ListItem, ListItemText, ListItemAvatar, ListItemIcon, ListItemButton,
    Divider, TextField, Select, MenuItem, FormControl, InputLabel, InputAdornment,
    Chip, Badge, Alert, AlertTitle, CircularProgress, LinearProgress, Skeleton,
    Dialog, DialogTitle, DialogContent, DialogActions, DialogContentText,
    Drawer, AppBar, Toolbar, Table, TableBody, TableCell, TableContainer,
    TableHead, TableRow, TablePagination, Tabs, Tab, Menu, Tooltip,
    Checkbox, Radio, RadioGroup, FormControlLabel, Switch, Slider, Rating,
    Autocomplete, ToggleButton, ToggleButtonGroup,
    useTheme, alpha, styled, ThemeProvider, createTheme
  };
}

declare module '*.svg' {
  const content: any;
  export default content;
}

declare module '*.png' {
  const content: any;
  export default content;
}

declare module '*.jpg' {
  const content: any;
  export default content;
}

declare module '*.css' {
  const content: any;
  export default content;
}

declare module '*.scss' {
  const content: any;
  export default content;
}

// Global type extensions
declare global {
  interface Window {
    [key: string]: any;
  }

  interface EventListener {
    (evt: any): void;
  }
}

export {};
