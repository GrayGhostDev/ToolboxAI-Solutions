import * as React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Grid2 from "@mui/material/Unstable_Grid2";
import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import LinearProgress from "@mui/material/LinearProgress";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import AddIcon from "@mui/icons-material/Add";
import AssessmentIcon from "@mui/icons-material/Assessment";

export default function Assessments() {
  return (
    <Grid2 container spacing={3}>
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center">
              <Typography variant="h5" sx={{ fontWeight: 600 }}>
                Assessments
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />}>
                Create Assessment
              </Button>
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Assessment Stats */}
      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Active Assessments
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                8
              </Typography>
              <Chip label="2 due today" size="small" color="warning" />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Pending Grading
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                23
              </Typography>
              <LinearProgress variant="determinate" value={65} />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Average Score
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                78%
              </Typography>
              <Chip label="+3% from last week" size="small" color="success" />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      <Grid2 size={{ xs: 12, md: 3 }}>
        <Card>
          <CardContent>
            <Stack spacing={1}>
              <Typography variant="caption" color="text.secondary">
                Completion Rate
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 700 }}>
                92%
              </Typography>
              <LinearProgress variant="determinate" value={92} color="success" />
            </Stack>
          </CardContent>
        </Card>
      </Grid2>

      {/* Recent Assessments */}
      <Grid2 size={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Recent Assessments
            </Typography>
            <Stack spacing={2}>
              {[
                { title: "Math Quiz - Fractions", type: "quiz", submissions: "18/20", avgScore: "82%" },
                { title: "Science Test - Solar System", type: "test", submissions: "15/20", avgScore: "75%" },
                { title: "Language Assignment", type: "assignment", submissions: "20/20", avgScore: "88%" },
                { title: "History Project", type: "project", submissions: "12/20", avgScore: "pending" },
              ].map((assessment, index) => (
                <Box
                  key={index}
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: "background.default",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Stack direction="row" spacing={2} alignItems="center">
                    <AssessmentIcon color="primary" />
                    <Stack>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {assessment.title}
                      </Typography>
                      <Stack direction="row" spacing={1}>
                        <Chip label={assessment.type} size="small" />
                        <Typography variant="caption" color="text.secondary">
                          Submissions: {assessment.submissions}
                        </Typography>
                      </Stack>
                    </Stack>
                  </Stack>
                  <Stack alignItems="flex-end">
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {assessment.avgScore}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Avg. Score
                    </Typography>
                  </Stack>
                </Box>
              ))}
            </Stack>
          </CardContent>
        </Card>
      </Grid2>
    </Grid2>
  );
}