import Backdrop from "@mui/material/Backdrop";
import CircularProgress from "@mui/material/CircularProgress";
import Typography from "@mui/material/Typography";
import Stack from "@mui/material/Stack";
import { Roblox3DLoader } from "../roblox/Roblox3DLoader";
import { useTheme } from "@mui/material";

interface Props {
  message?: string;
  use3DLoader?: boolean;
}

export function LoadingOverlay({ message = "Loading awesome stuff...", use3DLoader = true }: Props) {
  const theme = useTheme();

  return (
    <Backdrop
      sx={{
        color: "#fff",
        zIndex: (theme) => theme.zIndex.drawer + 1,
        backgroundColor: "rgba(15, 15, 46, 0.95)",
        backdropFilter: "blur(5px)",
      }}
      open={true}
    >
      {use3DLoader ? (
        <Roblox3DLoader
          message={message}
          variant="both"
          size="large"
          showBackground={true}
        />
      ) : (
        <Stack alignItems="center" spacing={2}>
          <CircularProgress color="inherit" size={60} />
          <Typography variant="h6">{message}</Typography>
        </Stack>
      )}
    </Backdrop>
  );
}