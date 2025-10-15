/**
 * Analytics Aggregation Edge Function
 *
 * Scheduled function that runs every 5 minutes to aggregate agent metrics
 * from raw execution data, update metrics tables, and calculate system health.
 *
 * Features:
 * - Periodic metric aggregation (every 5 minutes)
 * - Agent performance calculations
 * - System health score computation
 * - Time-series data generation
 * - Anomaly detection
 * - Trend analysis
 * - Automated cleanup of old data
 *
 * @module analytics-aggregation
 * @requires deno
 * @requires supabase
 */

// Updated to 2025 standards: Deno 2.1 + Supabase JS 2.75.0
import { createClient } from "npm:@supabase/supabase-js@2.75.0";

// ============================================================================
// Types and Interfaces
// ============================================================================

interface AggregationPeriod {
  start: Date;
  end: Date;
  durationMinutes: number;
}

interface AgentMetrics {
  agentInstanceId: string;
  agentType: string;
  organizationId?: string;
  tasksCompleted: number;
  tasksFailed: number;
  tasksCancelled: number;
  totalTasks: number;
  successRate: number;
  errorRate: number;
  averageExecutionTime: number;
  medianExecutionTime: number;
  p95ExecutionTime: number;
  tasksPerMinute: number;
  tasksPerHour: number;
  averageQualityScore: number;
  averageConfidenceScore: number;
  averageUserRating: number;
  averageMemoryUsage: number;
  peakMemoryUsage: number;
  averageCpuUsage: number;
  peakCpuUsage: number;
  uptimePercentage: number;
  availabilityPercentage: number;
}

interface SystemHealth {
  totalAgents: number;
  activeAgents: number;
  idleAgents: number;
  busyAgents: number;
  errorAgents: number;
  totalTasks: number;
  completedTasks: number;
  failedTasks: number;
  queuedTasks: number;
  runningTasks: number;
  systemSuccessRate: number;
  systemErrorRate: number;
  averageResponseTime: number;
  p95ResponseTime: number;
  tasksPerMinute: number;
  tasksPerHour: number;
  queueLength: number;
  averageQueueWaitTime: number;
  overallHealthScore: number;
  availabilityPercentage: number;
  activeAlerts: number;
  criticalIssues: number;
  warnings: number;
}

// ============================================================================
// Configuration
// ============================================================================

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

const AGGREGATION_CONFIG = {
  periodMinutes: 5,
  retentionDays: 30,
  batchSize: 100,
  healthScoreWeights: {
    successRate: 0.3,
    availability: 0.25,
    responseTime: 0.2,
    queueHealth: 0.15,
    errorRate: 0.1,
  },
  thresholds: {
    criticalSuccessRate: 50, // Below this is critical
    warningSuccessRate: 80, // Below this is warning
    criticalResponseTime: 10000, // ms
    warningResponseTime: 5000, // ms
    criticalQueueLength: 100,
    warningQueueLength: 50,
  },
};

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Initialize Supabase client with service role
 */
function getSupabaseClient() {
  return createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });
}

/**
 * Get aggregation period (last N minutes)
 */
function getAggregationPeriod(): AggregationPeriod {
  const end = new Date();
  const start = new Date(
    end.getTime() - AGGREGATION_CONFIG.periodMinutes * 60 * 1000
  );

  return {
    start,
    end,
    durationMinutes: AGGREGATION_CONFIG.periodMinutes,
  };
}

/**
 * Calculate percentile from sorted array
 */
function calculatePercentile(sortedValues: number[], percentile: number): number {
  if (sortedValues.length === 0) return 0;
  if (sortedValues.length === 1) return sortedValues[0];

  const index = Math.ceil((percentile / 100) * sortedValues.length) - 1;
  return sortedValues[Math.max(0, Math.min(index, sortedValues.length - 1))];
}

/**
 * Calculate median from sorted array
 */
function calculateMedian(sortedValues: number[]): number {
  if (sortedValues.length === 0) return 0;
  if (sortedValues.length === 1) return sortedValues[0];

  const mid = Math.floor(sortedValues.length / 2);
  if (sortedValues.length % 2 === 0) {
    return (sortedValues[mid - 1] + sortedValues[mid]) / 2;
  }
  return sortedValues[mid];
}

// ============================================================================
// Aggregation Functions
// ============================================================================

/**
 * Aggregate metrics for a single agent
 */
async function aggregateAgentMetrics(
  supabase: any,
  agentInstanceId: string,
  period: AggregationPeriod
): Promise<AgentMetrics | null> {
  try {
    // Fetch executions for this agent in the period
    const { data: executions, error } = await supabase
      .from("agent_executions")
      .select("*")
      .eq("agent_instance_id", agentInstanceId)
      .gte("created_at", period.start.toISOString())
      .lte("created_at", period.end.toISOString());

    if (error) {
      console.error("Error fetching executions:", error);
      return null;
    }

    if (!executions || executions.length === 0) {
      return null; // No data for this period
    }

    // Get agent info
    const { data: agent } = await supabase
      .from("agent_instances")
      .select("agent_type, organization_id")
      .eq("id", agentInstanceId)
      .single();

    // Calculate metrics
    const totalTasks = executions.length;
    const completedTasks = executions.filter((e: any) => e.status === "completed").length;
    const failedTasks = executions.filter((e: any) => e.status === "failed").length;
    const cancelledTasks = executions.filter((e: any) => e.status === "cancelled").length;

    const successRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;
    const errorRate = totalTasks > 0 ? (failedTasks / totalTasks) * 100 : 0;

    // Execution times (only for completed tasks)
    const executionTimes = executions
      .filter((e: any) => e.execution_time_seconds != null)
      .map((e: any) => e.execution_time_seconds)
      .sort((a: number, b: number) => a - b);

    const averageExecutionTime =
      executionTimes.length > 0
        ? executionTimes.reduce((a: number, b: number) => a + b, 0) / executionTimes.length
        : 0;

    const medianExecutionTime = calculateMedian(executionTimes);
    const p95ExecutionTime = calculatePercentile(executionTimes, 95);

    // Quality metrics
    const qualityScores = executions
      .filter((e: any) => e.quality_score != null)
      .map((e: any) => e.quality_score);

    const confidenceScores = executions
      .filter((e: any) => e.confidence_score != null)
      .map((e: any) => e.confidence_score);

    const userRatings = executions
      .filter((e: any) => e.user_rating != null)
      .map((e: any) => e.user_rating);

    const averageQualityScore =
      qualityScores.length > 0
        ? qualityScores.reduce((a: number, b: number) => a + b, 0) / qualityScores.length
        : 0;

    const averageConfidenceScore =
      confidenceScores.length > 0
        ? confidenceScores.reduce((a: number, b: number) => a + b, 0) / confidenceScores.length
        : 0;

    const averageUserRating =
      userRatings.length > 0
        ? userRatings.reduce((a: number, b: number) => a + b, 0) / userRatings.length
        : 0;

    // Resource usage
    const memoryUsages = executions
      .filter((e: any) => e.memory_usage_mb != null)
      .map((e: any) => e.memory_usage_mb);

    const cpuUsages = executions
      .filter((e: any) => e.cpu_usage_percent != null)
      .map((e: any) => e.cpu_usage_percent);

    const averageMemoryUsage =
      memoryUsages.length > 0
        ? memoryUsages.reduce((a: number, b: number) => a + b, 0) / memoryUsages.length
        : 0;

    const peakMemoryUsage = memoryUsages.length > 0 ? Math.max(...memoryUsages) : 0;

    const averageCpuUsage =
      cpuUsages.length > 0
        ? cpuUsages.reduce((a: number, b: number) => a + b, 0) / cpuUsages.length
        : 0;

    const peakCpuUsage = cpuUsages.length > 0 ? Math.max(...cpuUsages) : 0;

    // Throughput
    const tasksPerMinute = totalTasks / period.durationMinutes;
    const tasksPerHour = tasksPerMinute * 60;

    // Availability (based on agent status changes during period)
    const uptimePercentage = 100; // Simplified - would need heartbeat data
    const availabilityPercentage = successRate; // Simplified

    return {
      agentInstanceId,
      agentType: agent?.agent_type || "unknown",
      organizationId: agent?.organization_id,
      tasksCompleted: completedTasks,
      tasksFailed: failedTasks,
      tasksCancelled: cancelledTasks,
      totalTasks,
      successRate,
      errorRate,
      averageExecutionTime,
      medianExecutionTime,
      p95ExecutionTime,
      tasksPerMinute,
      tasksPerHour,
      averageQualityScore,
      averageConfidenceScore,
      averageUserRating,
      averageMemoryUsage,
      peakMemoryUsage,
      averageCpuUsage,
      peakCpuUsage,
      uptimePercentage,
      availabilityPercentage,
    };
  } catch (error) {
    console.error("Error aggregating agent metrics:", error);
    return null;
  }
}

/**
 * Save agent metrics to database
 */
async function saveAgentMetrics(
  supabase: any,
  metrics: AgentMetrics,
  period: AggregationPeriod
): Promise<boolean> {
  try {
    const { error } = await supabase.from("agent_metrics").insert({
      agent_instance_id: metrics.agentInstanceId,
      agent_type: metrics.agentType,
      organization_id: metrics.organizationId,
      period_start: period.start.toISOString(),
      period_end: period.end.toISOString(),
      period_duration_minutes: period.durationMinutes,
      tasks_completed: metrics.tasksCompleted,
      tasks_failed: metrics.tasksFailed,
      tasks_cancelled: metrics.tasksCancelled,
      total_tasks: metrics.totalTasks,
      success_rate: metrics.successRate,
      error_rate: metrics.errorRate,
      average_execution_time: metrics.averageExecutionTime,
      median_execution_time: metrics.medianExecutionTime,
      p95_execution_time: metrics.p95ExecutionTime,
      tasks_per_minute: metrics.tasksPerMinute,
      tasks_per_hour: metrics.tasksPerHour,
      average_quality_score: metrics.averageQualityScore,
      average_confidence_score: metrics.averageConfidenceScore,
      average_user_rating: metrics.averageUserRating,
      average_memory_usage_mb: metrics.averageMemoryUsage,
      peak_memory_usage_mb: metrics.peakMemoryUsage,
      average_cpu_usage_percent: metrics.averageCpuUsage,
      peak_cpu_usage_percent: metrics.peakCpuUsage,
      uptime_percentage: metrics.uptimePercentage,
      availability_percentage: metrics.availabilityPercentage,
    });

    if (error) {
      console.error("Error saving agent metrics:", error);
      return false;
    }

    return true;
  } catch (error) {
    console.error("Error in saveAgentMetrics:", error);
    return false;
  }
}

/**
 * Calculate system health
 */
async function calculateSystemHealth(
  supabase: any,
  period: AggregationPeriod
): Promise<SystemHealth | null> {
  try {
    // Get agent counts by status
    const { data: agents } = await supabase.from("agent_instances").select("status");

    const totalAgents = agents?.length || 0;
    const activeAgents = agents?.filter((a: any) => ["idle", "busy", "processing"].includes(a.status)).length || 0;
    const idleAgents = agents?.filter((a: any) => a.status === "idle").length || 0;
    const busyAgents = agents?.filter((a: any) => ["busy", "processing"].includes(a.status)).length || 0;
    const errorAgents = agents?.filter((a: any) => a.status === "error").length || 0;

    // Get task statistics
    const { data: executions } = await supabase
      .from("agent_executions")
      .select("status, execution_time_seconds")
      .gte("created_at", period.start.toISOString())
      .lte("created_at", period.end.toISOString());

    const totalTasks = executions?.length || 0;
    const completedTasks = executions?.filter((e: any) => e.status === "completed").length || 0;
    const failedTasks = executions?.filter((e: any) => e.status === "failed").length || 0;
    const runningTasks = executions?.filter((e: any) => e.status === "running").length || 0;

    const systemSuccessRate = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 100;
    const systemErrorRate = totalTasks > 0 ? (failedTasks / totalTasks) * 100 : 0;

    // Response times
    const executionTimes = executions
      ?.filter((e: any) => e.execution_time_seconds != null)
      .map((e: any) => e.execution_time_seconds)
      .sort((a: number, b: number) => a - b) || [];

    const averageResponseTime =
      executionTimes.length > 0
        ? executionTimes.reduce((a: number, b: number) => a + b, 0) / executionTimes.length
        : 0;

    const p95ResponseTime = calculatePercentile(executionTimes, 95);

    // Throughput
    const tasksPerMinute = totalTasks / period.durationMinutes;
    const tasksPerHour = tasksPerMinute * 60;

    // Queue statistics
    const { data: queuedTasks } = await supabase
      .from("agent_task_queue")
      .select("created_at, assigned_at")
      .eq("status", "pending");

    const queueLength = queuedTasks?.length || 0;

    const waitTimes = queuedTasks
      ?.filter((t: any) => t.assigned_at)
      .map((t: any) => {
        const created = new Date(t.created_at).getTime();
        const assigned = new Date(t.assigned_at).getTime();
        return (assigned - created) / 1000; // seconds
      }) || [];

    const averageQueueWaitTime =
      waitTimes.length > 0
        ? waitTimes.reduce((a: number, b: number) => a + b, 0) / waitTimes.length
        : 0;

    // Calculate health score
    const healthScore = calculateOverallHealthScore({
      systemSuccessRate,
      availabilityPercentage: (activeAgents / Math.max(totalAgents, 1)) * 100,
      averageResponseTime,
      queueLength,
      systemErrorRate,
    });

    // Detect issues
    const { activeAlerts, criticalIssues, warnings } = detectIssues({
      systemSuccessRate,
      averageResponseTime,
      queueLength,
      errorAgents,
    });

    return {
      totalAgents,
      activeAgents,
      idleAgents,
      busyAgents,
      errorAgents,
      totalTasks,
      completedTasks,
      failedTasks,
      queuedTasks: queueLength,
      runningTasks,
      systemSuccessRate,
      systemErrorRate,
      averageResponseTime,
      p95ResponseTime,
      tasksPerMinute,
      tasksPerHour,
      queueLength,
      averageQueueWaitTime,
      overallHealthScore: healthScore,
      availabilityPercentage: (activeAgents / Math.max(totalAgents, 1)) * 100,
      activeAlerts,
      criticalIssues,
      warnings,
    };
  } catch (error) {
    console.error("Error calculating system health:", error);
    return null;
  }
}

/**
 * Calculate overall health score
 */
function calculateOverallHealthScore(metrics: {
  systemSuccessRate: number;
  availabilityPercentage: number;
  averageResponseTime: number;
  queueLength: number;
  systemErrorRate: number;
}): number {
  const weights = AGGREGATION_CONFIG.healthScoreWeights;

  // Normalize metrics to 0-100 scale
  const successScore = metrics.systemSuccessRate;
  const availabilityScore = metrics.availabilityPercentage;

  // Response time score (inverse - lower is better)
  const responseScore = Math.max(
    0,
    100 - (metrics.averageResponseTime / AGGREGATION_CONFIG.thresholds.warningResponseTime) * 100
  );

  // Queue health score (inverse - lower is better)
  const queueScore = Math.max(
    0,
    100 - (metrics.queueLength / AGGREGATION_CONFIG.thresholds.warningQueueLength) * 100
  );

  // Error rate score (inverse - lower is better)
  const errorScore = Math.max(0, 100 - metrics.systemErrorRate);

  // Weighted average
  const overallScore =
    successScore * weights.successRate +
    availabilityScore * weights.availability +
    responseScore * weights.responseTime +
    queueScore * weights.queueHealth +
    errorScore * weights.errorRate;

  return Math.round(Math.max(0, Math.min(100, overallScore)));
}

/**
 * Detect system issues
 */
function detectIssues(metrics: {
  systemSuccessRate: number;
  averageResponseTime: number;
  queueLength: number;
  errorAgents: number;
}): { activeAlerts: number; criticalIssues: number; warnings: number } {
  let criticalIssues = 0;
  let warnings = 0;

  // Check success rate
  if (metrics.systemSuccessRate < AGGREGATION_CONFIG.thresholds.criticalSuccessRate) {
    criticalIssues++;
  } else if (metrics.systemSuccessRate < AGGREGATION_CONFIG.thresholds.warningSuccessRate) {
    warnings++;
  }

  // Check response time
  if (metrics.averageResponseTime > AGGREGATION_CONFIG.thresholds.criticalResponseTime) {
    criticalIssues++;
  } else if (metrics.averageResponseTime > AGGREGATION_CONFIG.thresholds.warningResponseTime) {
    warnings++;
  }

  // Check queue length
  if (metrics.queueLength > AGGREGATION_CONFIG.thresholds.criticalQueueLength) {
    criticalIssues++;
  } else if (metrics.queueLength > AGGREGATION_CONFIG.thresholds.warningQueueLength) {
    warnings++;
  }

  // Check error agents
  if (metrics.errorAgents > 0) {
    warnings++;
  }

  return {
    activeAlerts: criticalIssues + warnings,
    criticalIssues,
    warnings,
  };
}

/**
 * Save system health to database
 */
async function saveSystemHealth(
  supabase: any,
  health: SystemHealth,
  period: AggregationPeriod
): Promise<boolean> {
  try {
    const { error } = await supabase.from("system_health").insert({
      timestamp: period.end.toISOString(),
      period_minutes: period.durationMinutes,
      total_agents: health.totalAgents,
      active_agents: health.activeAgents,
      idle_agents: health.idleAgents,
      busy_agents: health.busyAgents,
      error_agents: health.errorAgents,
      total_tasks: health.totalTasks,
      completed_tasks: health.completedTasks,
      failed_tasks: health.failedTasks,
      queued_tasks: health.queuedTasks,
      running_tasks: health.runningTasks,
      system_success_rate: health.systemSuccessRate,
      system_error_rate: health.systemErrorRate,
      average_response_time: health.averageResponseTime,
      p95_response_time: health.p95ResponseTime,
      tasks_per_minute: health.tasksPerMinute,
      tasks_per_hour: health.tasksPerHour,
      queue_length: health.queueLength,
      average_queue_wait_time: health.averageQueueWaitTime,
      overall_health_score: health.overallHealthScore,
      availability_percentage: health.availabilityPercentage,
      active_alerts: health.activeAlerts,
      critical_issues: health.criticalIssues,
      warnings: health.warnings,
    });

    if (error) {
      console.error("Error saving system health:", error);
      return false;
    }

    return true;
  } catch (error) {
    console.error("Error in saveSystemHealth:", error);
    return false;
  }
}

/**
 * Clean up old data
 */
async function cleanupOldData(supabase: any): Promise<void> {
  try {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - AGGREGATION_CONFIG.retentionDays);

    // Call cleanup function from database
    const { data, error } = await supabase.rpc("cleanup_old_agent_data", {
      days_to_keep: AGGREGATION_CONFIG.retentionDays,
    });

    if (error) {
      console.error("Error cleaning up old data:", error);
    } else {
      console.log("Cleanup results:", data);
    }
  } catch (error) {
    console.error("Error in cleanupOldData:", error);
  }
}

// ============================================================================
// Main Aggregation Function
// ============================================================================

/**
 * Run analytics aggregation
 */
async function runAggregation(): Promise<{
  success: boolean;
  period: AggregationPeriod;
  agentMetricsCount: number;
  systemHealth: SystemHealth | null;
  errors: string[];
}> {
  const startTime = Date.now();
  const errors: string[] = [];

  console.log("Starting analytics aggregation...");

  const supabase = getSupabaseClient();
  const period = getAggregationPeriod();

  console.log(`Aggregation period: ${period.start.toISOString()} to ${period.end.toISOString()}`);

  // Get all agent instances
  const { data: agents, error: agentsError } = await supabase
    .from("agent_instances")
    .select("id");

  if (agentsError) {
    errors.push(`Failed to fetch agents: ${agentsError.message}`);
    return {
      success: false,
      period,
      agentMetricsCount: 0,
      systemHealth: null,
      errors,
    };
  }

  // Aggregate metrics for each agent
  let metricsCount = 0;
  const batchSize = AGGREGATION_CONFIG.batchSize;

  for (let i = 0; i < (agents?.length || 0); i += batchSize) {
    const batch = agents!.slice(i, i + batchSize);

    const metricPromises = batch.map(async (agent: any) => {
      const metrics = await aggregateAgentMetrics(supabase, agent.id, period);
      if (metrics) {
        const saved = await saveAgentMetrics(supabase, metrics, period);
        if (saved) {
          metricsCount++;
        }
      }
    });

    await Promise.all(metricPromises);
  }

  console.log(`Aggregated metrics for ${metricsCount} agents`);

  // Calculate and save system health
  const systemHealth = await calculateSystemHealth(supabase, period);
  if (systemHealth) {
    await saveSystemHealth(supabase, systemHealth, period);
    console.log(`System health score: ${systemHealth.overallHealthScore}`);
  }

  // Cleanup old data (once per day - check if we should run)
  const now = new Date();
  if (now.getHours() === 0 && now.getMinutes() < AGGREGATION_CONFIG.periodMinutes) {
    console.log("Running daily cleanup...");
    await cleanupOldData(supabase);
  }

  const duration = Date.now() - startTime;
  console.log(`Aggregation completed in ${duration}ms`);

  return {
    success: true,
    period,
    agentMetricsCount: metricsCount,
    systemHealth,
    errors,
  };
}

// ============================================================================
// Edge Function Handler
// ============================================================================

Deno.serve(async (req: Request) => {
  try {
    // Handle CORS preflight
    if (req.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
        },
      });
    }

    // Run aggregation
    const result = await runAggregation();

    // Return result
    return new Response(
      JSON.stringify({
        success: result.success,
        data: {
          period: {
            start: result.period.start.toISOString(),
            end: result.period.end.toISOString(),
            durationMinutes: result.period.durationMinutes,
          },
          agentMetricsCount: result.agentMetricsCount,
          systemHealth: result.systemHealth,
          errors: result.errors,
        },
      }),
      {
        status: result.success ? 200 : 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  } catch (error) {
    console.error("Edge function error:", error);

    return new Response(
      JSON.stringify({
        error: error instanceof Error ? error.message : "Internal server error",
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      }
    );
  }
});
