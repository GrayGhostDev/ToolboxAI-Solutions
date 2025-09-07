import * as React from "react";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import Grid2 from "@mui/material/Unstable_Grid2";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  RadialBarChart,
  RadialBar,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { UserRole } from "../../types/roles";
import { useTheme } from "@mui/material/styles";

const weeklyData = [
  { day: "Mon", xp: 120, hours: 2.5 },
  { day: "Tue", xp: 180, hours: 3.2 },
  { day: "Wed", xp: 140, hours: 2.8 },
  { day: "Thu", xp: 220, hours: 4.1 },
  { day: "Fri", xp: 190, hours: 3.5 },
  { day: "Sat", xp: 60, hours: 1.2 },
  { day: "Sun", xp: 40, hours: 0.8 },
];

const subjectData = [
  { subject: "Math", mastery: 78, avgScore: 85 },
  { subject: "Science", mastery: 64, avgScore: 72 },
  { subject: "Language", mastery: 82, avgScore: 88 },
  { subject: "Arts", mastery: 70, avgScore: 75 },
  { subject: "Tech", mastery: 90, avgScore: 92 },
];

const levelData = [{ name: "Level Progress", value: 65, fill: "#2563EB" }];

const skillsData = [
  { skill: "Problem Solving", A: 85, fullMark: 100 },
  { skill: "Critical Thinking", A: 78, fullMark: 100 },
  { skill: "Creativity", A: 92, fullMark: 100 },
  { skill: "Collaboration", A: 70, fullMark: 100 },
  { skill: "Communication", A: 88, fullMark: 100 },
  { skill: "Digital Literacy", A: 95, fullMark: 100 },
];

const activityData = [
  { name: "Lessons", value: 35, color: "#2563EB" },
  { name: "Quizzes", value: 25, color: "#22C55E" },
  { name: "Projects", value: 20, color: "#FACC15" },
  { name: "Games", value: 20, color: "#9333EA" },
];

export function ProgressCharts({ role }: { role: UserRole }) {
  const theme = useTheme();

  const chartColors = {
    primary: theme.palette.primary.main,
    secondary: theme.palette.secondary.main,
    warning: theme.palette.warning.main,
    info: theme.palette.info.main,
    success: theme.palette.success.main,
  };

  return (
    <Grid2 container spacing={3}>
      {/* Weekly XP Progress */}
      <Grid2 size={{ xs: 12, md: 6 }}>
        <Card role="region" aria-label="Weekly XP chart">
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Weekly {role === "Student" ? "XP Progress" : "Class Activity"}
            </Typography>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer>
                <LineChart data={weeklyData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis dataKey="day" stroke={theme.palette.text.secondary} />
                  <YAxis stroke={theme.palette.text.secondary} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="xp"
                    stroke={chartColors.primary}
                    strokeWidth={3}
                    dot={{ fill: chartColors.primary, r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                  {role === "Teacher" && (
                    <Line
                      type="monotone"
                      dataKey="hours"
                      stroke={chartColors.secondary}
                      strokeWidth={3}
                      dot={{ fill: chartColors.secondary, r: 4 }}
                      activeDot={{ r: 6 }}
                    />
                  )}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </Grid2>

      {/* Subject Mastery */}
      <Grid2 size={{ xs: 12, md: 6 }}>
        <Card role="region" aria-label="Subject mastery bar chart">
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Subject {role === "Student" ? "Mastery" : "Performance"}
            </Typography>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer>
                <BarChart data={subjectData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                  <XAxis dataKey="subject" stroke={theme.palette.text.secondary} />
                  <YAxis stroke={theme.palette.text.secondary} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                  <Bar dataKey="mastery" fill={chartColors.primary} radius={[8, 8, 0, 0]} />
                  {role === "Teacher" && (
                    <Bar dataKey="avgScore" fill={chartColors.secondary} radius={[8, 8, 0, 0]} />
                  )}
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </Grid2>

      {/* Skills Radar Chart */}
      {role === "Student" && (
        <Grid2 size={{ xs: 12, md: 6 }}>
          <Card role="region" aria-label="Skills radar chart">
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Skill Development
              </Typography>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <RadarChart data={skillsData}>
                    <PolarGrid stroke={theme.palette.divider} />
                    <PolarAngleAxis dataKey="skill" stroke={theme.palette.text.secondary} />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      stroke={theme.palette.text.secondary}
                    />
                    <Radar
                      name="Skills"
                      dataKey="A"
                      stroke={chartColors.primary}
                      fill={chartColors.primary}
                      fillOpacity={0.6}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 8,
                      }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </Grid2>
      )}

      {/* Activity Distribution */}
      <Grid2 size={{ xs: 12, md: role === "Student" ? 6 : 4 }}>
        <Card role="region" aria-label="Activity distribution pie chart">
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
              Activity Distribution
            </Typography>
            <div style={{ width: "100%", height: 300 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={activityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {activityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: theme.palette.background.paper,
                      border: `1px solid ${theme.palette.divider}`,
                      borderRadius: 8,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </Grid2>

      {/* Level Progress (for Students) or Completion Rate (for others) */}
      {role !== "Parent" && (
        <Grid2 size={{ xs: 12, md: 4 }}>
          <Card role="region" aria-label="Progress radial chart">
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                {role === "Student" ? "Level Progress" : "Completion Rate"}
              </Typography>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <RadialBarChart
                    cx="50%"
                    cy="50%"
                    innerRadius="60%"
                    outerRadius="90%"
                    barSize={10}
                    data={levelData}
                    startAngle={90}
                    endAngle={-270}
                  >
                    <RadialBar
                      background
                      dataKey="value"
                      cornerRadius={12}
                      fill={chartColors.primary}
                    />
                    <Legend
                      iconSize={10}
                      layout="horizontal"
                      verticalAlign="bottom"
                      align="center"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 8,
                      }}
                    />
                  </RadialBarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </Grid2>
      )}

      {/* Monthly Trend (for Teachers and Admins) */}
      {(role === "Teacher" || role === "Admin") && (
        <Grid2 size={{ xs: 12, md: 4 }}>
          <Card role="region" aria-label="Monthly trend">
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                Monthly Trend
              </Typography>
              <div style={{ width: "100%", height: 300 }}>
                <ResponsiveContainer>
                  <LineChart
                    data={[
                      { month: "Jan", students: 82 },
                      { month: "Feb", students: 85 },
                      { month: "Mar", students: 88 },
                      { month: "Apr", students: 86 },
                      { month: "May", students: 90 },
                    ]}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                    <XAxis dataKey="month" stroke={theme.palette.text.secondary} />
                    <YAxis stroke={theme.palette.text.secondary} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: theme.palette.background.paper,
                        border: `1px solid ${theme.palette.divider}`,
                        borderRadius: 8,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="students"
                      stroke={chartColors.success}
                      strokeWidth={3}
                      dot={{ fill: chartColors.success, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </Grid2>
      )}
    </Grid2>
  );
}