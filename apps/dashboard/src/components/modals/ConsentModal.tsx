import * as React from "react";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import { recordConsent } from "../../services/api";
import { useAppSelector } from "../../store";

interface Props {
  open: boolean;
  onClose: (accepted: boolean) => void;
}

export function ConsentModal({ open, onClose }: Props) {
  const [coppaChecked, setCoppaChecked] = React.useState(false);
  const [ferpaChecked, setFerpaChecked] = React.useState(false);
  const [gdprChecked, setGdprChecked] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const userId = useAppSelector((s) => s.user.userId);

  const allChecked = coppaChecked && ferpaChecked && gdprChecked;

  const handleAccept = async () => {
    if (!allChecked || !userId) return;

    setLoading(true);
    try {
      await Promise.all([
        recordConsent("coppa", userId),
        recordConsent("ferpa", userId),
        recordConsent("gdpr", userId),
      ]);
      onClose(true);
    } catch (error) {
      console.error("Failed to record consent:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={() => onClose(false)}
      aria-labelledby="consent-title"
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle id="consent-title">Parental Consent & Privacy Agreement</DialogTitle>
      <DialogContent>
        <Alert severity="info" sx={{ mb: 3 }}>
          To ensure the safety and privacy of students, we require parental consent in compliance
          with educational privacy laws.
        </Alert>

        <Stack spacing={2}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Please review and accept the following:
          </Typography>

          <FormControlLabel
            control={
              <Checkbox
                checked={coppaChecked}
                onChange={(e) => setCoppaChecked(e.target.checked)}
              />
            }
            label={
              <Stack>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  COPPA Compliance (Children's Online Privacy Protection Act)
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  I am a parent/guardian and consent to my child's participation in accordance with
                  COPPA regulations for children under 13.
                </Typography>
              </Stack>
            }
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={ferpaChecked}
                onChange={(e) => setFerpaChecked(e.target.checked)}
              />
            }
            label={
              <Stack>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  FERPA Compliance (Family Educational Rights and Privacy Act)
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  I understand and consent to the educational record keeping and sharing practices
                  as outlined in our FERPA policy.
                </Typography>
              </Stack>
            }
          />

          <FormControlLabel
            control={
              <Checkbox checked={gdprChecked} onChange={(e) => setGdprChecked(e.target.checked)} />
            }
            label={
              <Stack>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  GDPR Compliance (General Data Protection Regulation)
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  I consent to the processing of personal data in accordance with GDPR requirements
                  and understand my rights regarding data protection.
                </Typography>
              </Stack>
            }
          />
        </Stack>

        <Typography variant="caption" color="text.secondary" sx={{ mt: 3, display: "block" }}>
          By accepting, you confirm that you have read and understood our
          <a href="/privacy.html" target="_blank" rel="noopener noreferrer"> Privacy Policy</a>
          &nbsp;and
          <a href="/terms.html" target="_blank" rel="noopener noreferrer"> Terms of Service</a>.
          You can withdraw consent at any time through your account settings.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => onClose(false)}>Cancel</Button>
        <Button
          disabled={!allChecked || loading}
          variant="contained"
          onClick={handleAccept}
        >
          {loading ? "Processing..." : "Accept & Continue"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}