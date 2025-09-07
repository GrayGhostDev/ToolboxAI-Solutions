import React from "react";
import { Card, CardContent, Typography } from "@mui/material";

export default function Avatar() {
  return (
    <Card>
      <CardContent>
        <Typography variant="h5" gutterBottom>Avatar</Typography>
        <Typography variant="body2" color="text.secondary">
          Avatar functionality will be available here.
        </Typography>
      </CardContent>
    </Card>
  );
}
