import * as React from "react";
import Alert from "@mui/material/Alert";
import Link from "@mui/material/Link";
import Snackbar from "@mui/material/Snackbar";
import Button from "@mui/material/Button";

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
            <Button color="inherit" size="small" onClick={decline}>Decline</Button>
            <Button color="inherit" size="small" onClick={accept}>Accept</Button>
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
