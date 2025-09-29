import { Box, Button, Typography, Paper, Stack, Grid, Container, IconButton, Avatar, Card, CardContent, CardActions, List, ListItem, ListItemText, Divider, TextField, Select, MenuItem, Chip, Badge, Alert, CircularProgress, LinearProgress, Dialog, DialogTitle, DialogContent, DialogActions, Drawer, AppBar, Toolbar, Tabs, Tab, Menu, Tooltip, Checkbox, Radio, RadioGroup, FormControl, FormControlLabel, InputLabel, Switch, Slider, Rating, Autocomplete, Skeleton, Table } from '../../utils/mui-imports';
import * as React from "react";

export default function CookieBanner() {
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    if (typeof window !== 'undefined') {
      const consent = localStorage.getItem('cookie_consent');
      if (!consent) setOpen(true);
    }
  }, []);

  const accept = () => {
    localStorage.setItem('cookie_consent', 'accepted');
    setOpen(false);
  };

  const decline = () => {
    localStorage.setItem('cookie_consent', 'declined');
    setOpen(false);
  };

  return (
    <Snackbar
      open={open}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
    >
      <Alert
        severity="info"
        variant="filled"
        action={
          <>
            <Button color="inherit" size="small" onClick={(e: React.MouseEvent) => decline}>Decline</Button>
            <Button color="inherit" size="small" onClick={(e: React.MouseEvent) => accept}>Accept</Button>
          </>
        }
      >
        We use cookies to operate and improve the service. See our{' '}
        <Link href="/cookies.html" target="_blank" rel="noopener noreferrer" color="inherit" underline="always">
          Cookie Policy
        </Link>.
      </Alert>
    </Snackbar>
  );
}
