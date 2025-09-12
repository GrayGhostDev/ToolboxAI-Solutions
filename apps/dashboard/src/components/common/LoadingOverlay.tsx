import Backdrop from "@mui/material/Backdrop";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";

interface Props {
  message?: string;
}

export function LoadingOverlay({ message = "Loading..." }: Props) {
  return (
    <Backdrop
      sx={{
        color: "#fff",
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: "rgba(0, 0, 0, 0.8)",
      }}
      open={true}
    >
      <Stack alignItems="center" spacing={2}>
        <CircularProgress color="inherit" size={60} />
        <Typography variant="h6">{message}</Typography>
      </Stack>
    </Backdrop>
  );
}