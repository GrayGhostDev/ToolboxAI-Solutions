"""Analytics & Reporting API Endpoints for ToolBoxAI

Provides comprehensive analytics and reporting capabilities:
- Learning effectiveness analytics
- Usage metrics and engagement tracking
- Performance reporting for educators
- System health and monitoring endpoints
- Real-time dashboard data
- Advanced data visualization support
"""

import logging
import uuid
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, field_validator, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

# Import authentication and dependencies
try:
    from apps.backend.api.auth.auth import get_current_user, require_role, require_any_role
    from apps.backend.core.deps import get_db
    from apps.backend.core.security.rate_limit_manager import rate_limit
except ImportError:
    # Fallback for development
    def get_current_user():
        return {"id": "test", "role": "teacher", "email": "test@example.com"}
    def require_role(role): return lambda: None
    def require_any_role(roles): return lambda: None
    def get_db(): return None
    def rate_limit(requests=60): return lambda: None

# Import models and services
try:
    from apps.backend.models.schemas import User, BaseResponse
    from apps.backend.services.pusher import trigger_event
except ImportError:
    class User(BaseModel):
        id: str
        email: str
        role: str
    
    class BaseResponse(BaseModel):
        success: bool = True
        message: str = ""
        timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    async def trigger_event(channel, event, data): pass

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/analytics", tags=["Analytics & Reporting"])

# Enums
class MetricType(str, Enum):
    """Types of metrics to track"""
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"
    PROGRESS = "progress"
    USAGE = "usage"
    COMPLETION = "completion"
    RETENTION = "retention"
    SATISFACTION = "satisfaction"
    SYSTEM = "system"

class TimeGranularity(str, Enum):
    """Time granularity for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class ReportType(str, Enum):
    """Types of reports"""
    STUDENT_PROGRESS = "student_progress"
    CLASS_PERFORMANCE = "class_performance"
    CURRICULUM_EFFECTIVENESS = "curriculum_effectiveness"
    ENGAGEMENT_ANALYSIS = "engagement_analysis"
    SYSTEM_USAGE = "system_usage"
    LEARNING_OUTCOMES = "learning_outcomes"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    INTERVENTION_RECOMMENDATIONS = "intervention_recommendations"

class VisualizationType(str, Enum):
    """Types of data visualizations"""
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    HEATMAP = "heatmap"
    HISTOGRAM = "histogram"
    BOX_PLOT = "box_plot"
    AREA_CHART = "area_chart"

class AggregationMethod(str, Enum):
    """Data aggregation methods"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MAX = "max"
    MIN = "min"
    MEDIAN = "median"
    PERCENTILE = "percentile"

# Request Models
class AnalyticsQuery(BaseModel):
    """Request for analytics data"""
    metric_types: List[MetricType] = Field(..., min_items=1)
    start_date: datetime = Field(..., description="Start date for analytics period")
    end_date: datetime = Field(..., description="End date for analytics period")
    granularity: TimeGranularity = TimeGranularity.DAY
    filters: Dict[str, Any] = Field(default_factory=dict)
    aggregation_method: AggregationMethod = AggregationMethod.AVERAGE
    include_comparisons: bool = Field(False, description="Include period-over-period comparisons")
    include_benchmarks: bool = Field(False, description="Include benchmark data")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date and v <= start_date:
            raise ValueError('End date must be after start date')
        if start_date and (v - start_date).days > 365:
            raise ValueError('Date range cannot exceed 365 days')
        return v
    
    model_config = ConfigDict(from_attributes=True)

class ReportRequest(BaseModel):
    """Request to generate a report"""
    report_type: ReportType
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
    date_range: Dict[str, datetime] = Field(..., description="start_date and end_date")
    format: str = Field("json", description="json, pdf, csv, xlsx")
    recipients: List[str] = Field(default_factory=list, description="Email addresses for report delivery")
    schedule: Optional[Dict[str, Any]] = Field(None, description="Scheduling configuration for recurring reports")
    
    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v):
        if 'start_date' not in v or 'end_date' not in v:
            raise ValueError('date_range must include start_date and end_date')
        if v['end_date'] <= v['start_date']:
            raise ValueError('end_date must be after start_date')
        return v
    
    model_config = ConfigDict(from_attributes=True)

class DashboardConfigRequest(BaseModel):
    """Request to configure dashboard widgets"""
    dashboard_name: str = Field(..., min_length=1, max_length=100)
    widgets: List[Dict[str, Any]] = Field(..., min_items=1, max_items=20)
    layout: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval: int = Field(300, ge=30, le=3600, description="Refresh interval in seconds")
    is_default: bool = Field(False)
    sharing_settings: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class LearningAnalyticsRequest(BaseModel):
    """Request for learning-specific analytics"""
    student_ids: Optional[List[str]] = None
    class_ids: Optional[List[str]] = None
    subject_areas: Optional[List[str]] = None
    competency_areas: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    assessment_types: Optional[List[str]] = None
    time_period: Dict[str, datetime] = Field(..., description="start_date and end_date")
    include_predictions: bool = Field(False)
    include_recommendations: bool = Field(True)
    
    model_config = ConfigDict(from_attributes=True)

# Response Models
class MetricDataPoint(BaseModel):
    """Individual metric data point"""
    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class MetricSeries(BaseModel):
    """Time series of metric data"""
    metric_type: MetricType
    metric_name: str
    unit: str
    data_points: List[MetricDataPoint]
    aggregation_method: AggregationMethod
    summary_statistics: Dict[str, float] = Field(default_factory=dict)
    trend_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class AnalyticsResponse(BaseModel):
    """Response containing analytics data"""
    query_id: str
    metric_series: List[MetricSeries]
    period_summary: Dict[str, Any]
    comparisons: Optional[Dict[str, Any]] = None
    benchmarks: Optional[Dict[str, Any]] = None
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    generated_at: datetime
    query_execution_time_ms: float
    
    model_config = ConfigDict(from_attributes=True)

class ReportResponse(BaseModel):
    """Response for report generation"""
    report_id: str
    report_type: ReportType
    title: str
    status: str = "generated"
    file_url: Optional[str] = None
    preview_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime
    generated_by: str
    file_size_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class DashboardWidget(BaseModel):
    """Dashboard widget configuration and data"""
    widget_id: str
    widget_type: str
    title: str
    position: Dict[str, int] = Field(default_factory=dict)
    size: Dict[str, int] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DashboardResponse(BaseModel):
    """Dashboard configuration and data"""
    dashboard_id: str
    dashboard_name: str
    widgets: List[DashboardWidget]
    layout: Dict[str, Any]
    refresh_interval: int
    last_updated: datetime
    created_by: str
    is_default: bool
    sharing_settings: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)

class LearningAnalyticsResponse(BaseModel):
    """Learning-specific analytics response"""
    analysis_id: str
    student_performance: Dict[str, Any] = Field(default_factory=dict)
    class_performance: Dict[str, Any] = Field(default_factory=dict)
    competency_analysis: Dict[str, Any] = Field(default_factory=dict)
    learning_progression: List[Dict[str, Any]] = Field(default_factory=list)
    engagement_metrics: Dict[str, Any] = Field(default_factory=dict)
    at_risk_students: List[Dict[str, Any]] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    predictions: Optional[Dict[str, Any]] = None
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SystemHealthMetrics(BaseModel):
    """System health and performance metrics"""
    system_uptime: float
    response_time_avg: float
    error_rate: float
    active_users: int
    concurrent_sessions: int
    resource_utilization: Dict[str, float]
    database_performance: Dict[str, Any]
    api_performance: Dict[str, Any]
    recent_alerts: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EngagementAnalytics(BaseModel):
    """User engagement analytics"""
    total_active_users: int
    daily_active_users: int
    weekly_active_users: int
    monthly_active_users: int
    session_duration_avg: float
    page_views_total: int
    feature_usage: Dict[str, int]
    user_retention: Dict[str, float]
    engagement_score: float
    churn_rate: float
    most_popular_content: List[Dict[str, Any]]
    
    model_config = ConfigDict(from_attributes=True)

# Mock data stores
_mock_analytics_cache: Dict[str, Any] = {}
_mock_reports_db: Dict[str, ReportResponse] = {}
_mock_dashboards_db: Dict[str, DashboardResponse] = {}
_mock_learning_analytics: Dict[str, LearningAnalyticsResponse] = {}

# Utility functions
def generate_mock_metrics(metric_type: MetricType, start_date: datetime, end_date: datetime, granularity: TimeGranularity) -> List[MetricDataPoint]:
    """Generate mock metric data points"""
    import random
    import math
    
    data_points = []
    current = start_date
    
    # Determine time delta based on granularity
    if granularity == TimeGranularity.HOUR:
        delta = timedelta(hours=1)
    elif granularity == TimeGranularity.DAY:
        delta = timedelta(days=1)
    elif granularity == TimeGranularity.WEEK:
        delta = timedelta(weeks=1)
    elif granularity == TimeGranularity.MONTH:
        delta = timedelta(days=30)
    else:
        delta = timedelta(days=1)
    
    base_value = 50.0
    if metric_type == MetricType.ENGAGEMENT:
        base_value = 75.0
    elif metric_type == MetricType.PERFORMANCE:
        base_value = 85.0
    elif metric_type == MetricType.COMPLETION:
        base_value = 80.0
    
    while current <= end_date:
        # Add some realistic variation
        variation = random.uniform(-15, 15)
        trend = math.sin((current - start_date).days * 0.1) * 10  # Seasonal trend
        value = max(0, base_value + variation + trend)
        
        data_points.append(MetricDataPoint(
            timestamp=current,
            value=round(value, 2),
            metadata={"raw_value": value, "trend_component": trend}
        ))
        
        current += delta
    
    return data_points

def calculate_summary_statistics(data_points: List[MetricDataPoint]) -> Dict[str, float]:
    """Calculate summary statistics for metric data"""
    if not data_points:
        return {}
    
    values = [dp.value for dp in data_points]
    
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "std_dev": round(statistics.stdev(values) if len(values) > 1 else 0, 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "sum": round(sum(values), 2)
    }

def analyze_trend(data_points: List[MetricDataPoint]) -> Dict[str, Any]:
    """Analyze trend in metric data"""
    if len(data_points) < 2:
        return {"trend": "insufficient_data"}
    
    values = [dp.value for dp in data_points]
    
    # Simple linear trend analysis
    first_half = values[:len(values)//2]
    second_half = values[len(values)//2:]
    
    first_avg = statistics.mean(first_half)
    second_avg = statistics.mean(second_half)
    
    change_percentage = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
    
    if change_percentage > 5:
        trend_direction = "increasing"
    elif change_percentage < -5:
        trend_direction = "decreasing"
    else:
        trend_direction = "stable"
    
    return {
        "trend": trend_direction,
        "change_percentage": round(change_percentage, 2),
        "first_period_avg": round(first_avg, 2),
        "second_period_avg": round(second_avg, 2)
    }

async def notify_analytics_update(event_type: str, data: Dict[str, Any], user_id: str):
    """Notify about analytics updates"""
    try:
        await trigger_event(
            "analytics-updates",
            f"analytics.{event_type}",
            {
                "data": data,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to send analytics update notification: {e}")

# Initialize some mock data
def initialize_mock_dashboards():
    """Initialize mock dashboard configurations"""
    default_dashboard = DashboardResponse(
        dashboard_id="default_teacher_dashboard",
        dashboard_name="Teacher Overview",
        widgets=[
            DashboardWidget(
                widget_id="engagement_chart",
                widget_type="line_chart",
                title="Student Engagement Trends",
                position={"x": 0, "y": 0},
                size={"width": 6, "height": 4},
                configuration={"metric_type": "engagement", "time_period": "7d"},
                last_updated=datetime.now(timezone.utc)
            ),
            DashboardWidget(
                widget_id="performance_summary",
                widget_type="bar_chart",
                title="Class Performance Summary",
                position={"x": 6, "y": 0},
                size={"width": 6, "height": 4},
                configuration={"metric_type": "performance", "group_by": "subject"},
                last_updated=datetime.now(timezone.utc)
            )
        ],
        layout={"columns": 12, "row_height": 100},
        refresh_interval=300,
        last_updated=datetime.now(timezone.utc),
        created_by="system",
        is_default=True,
        sharing_settings={"public": False, "roles": ["teacher"]}
    )
    
    _mock_dashboards_db["default_teacher_dashboard"] = default_dashboard

# Initialize mock data on module load
initialize_mock_dashboards()

# Endpoints

@router.post("/query", response_model=AnalyticsResponse, status_code=status.HTTP_200_OK)
@rate_limit(requests=30)  # 30 analytics queries per minute
async def query_analytics(
    request: AnalyticsQuery,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Query analytics data with flexible filtering and aggregation.
    
    Rate limit: 30 requests per minute
    """
    try:
        query_start_time = datetime.now(timezone.utc)
        query_id = str(uuid.uuid4())
        
        # Generate metric series for each requested metric type
        metric_series = []
        
        for metric_type in request.metric_types:
            # Generate mock data points
            data_points = generate_mock_metrics(
                metric_type,
                request.start_date,
                request.end_date,
                request.granularity
            )
            
            # Calculate summary statistics
            summary_stats = calculate_summary_statistics(data_points)
            
            # Analyze trend
            trend_analysis = analyze_trend(data_points)
            
            # Create metric series
            series = MetricSeries(
                metric_type=metric_type,
                metric_name=metric_type.value.replace('_', ' ').title(),
                unit="percentage" if metric_type in [MetricType.ENGAGEMENT, MetricType.PERFORMANCE] else "count",
                data_points=data_points,
                aggregation_method=request.aggregation_method,
                summary_statistics=summary_stats,
                trend_analysis=trend_analysis
            )
            
            metric_series.append(series)
        
        # Generate period summary
        period_summary = {
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "total_data_points": sum(len(series.data_points) for series in metric_series),
            "metrics_analyzed": len(request.metric_types),
            "date_range_days": (request.end_date - request.start_date).days
        }
        
        # Generate insights
        insights = [
            "Engagement levels show consistent growth over the selected period",
            "Performance metrics indicate strong learning outcomes",
            "Usage patterns suggest optimal learning times between 9-11 AM"
        ]
        
        # Generate recommendations
        recommendations = [
            "Consider increasing interactive content during peak engagement hours",
            "Implement personalized learning paths for underperforming students",
            "Schedule challenging content during high-performance periods"
        ]
        
        # Calculate execution time
        execution_time = (datetime.now(timezone.utc) - query_start_time).total_seconds() * 1000
        
        response = AnalyticsResponse(
            query_id=query_id,
            metric_series=metric_series,
            period_summary=period_summary,
            insights=insights,
            recommendations=recommendations,
            generated_at=datetime.now(timezone.utc),
            query_execution_time_ms=execution_time
        )
        
        # Cache the response
        _mock_analytics_cache[query_id] = response
        
        # Background notification
        background_tasks.add_task(
            notify_analytics_update,
            "query_executed",
            {"query_id": query_id, "metrics": [m.value for m in request.metric_types]},
            current_user["id"]
        )
        
        logger.info(f"Analytics query executed: {query_id} by user {current_user['id']}")
        return response
        
    except Exception as e:
        logger.error(f"Error executing analytics query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute analytics query"
        )

@router.post("/reports", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests=10)  # 10 report generations per minute
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"]))
):
    """
    Generate a comprehensive report.
    
    Requires: Teacher or Admin role
    Rate limit: 10 requests per minute
    """
    try:
        report_id = str(uuid.uuid4())
        
        # Mock report generation (would integrate with actual report engine)
        report = ReportResponse(
            report_id=report_id,
            report_type=request.report_type,
            title=request.title,
            status="generated",
            file_url=f"/api/v1/analytics/reports/{report_id}/download",
            preview_data={
                "summary": f"Report '{request.title}' covering period from {request.date_range['start_date']} to {request.date_range['end_date']}",
                "key_metrics": {
                    "total_students": 150,
                    "average_performance": 85.2,
                    "completion_rate": 78.5
                },
                "highlights": [
                    "Strong performance in Mathematics",
                    "Engagement levels above benchmark",
                    "Consistent improvement trends"
                ]
            },
            metadata={
                "format": request.format,
                "parameters": request.parameters,
                "filters_applied": request.filters,
                "page_count": 15,
                "chart_count": 8
            },
            generated_at=datetime.now(timezone.utc),
            generated_by=current_user["id"],
            file_size_bytes=2048576,  # 2MB mock size
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        # Store report
        _mock_reports_db[report_id] = report
        
        # Background notification
        background_tasks.add_task(
            notify_analytics_update,
            "report_generated",
            {"report_id": report_id, "report_type": request.report_type.value, "title": request.title},
            current_user["id"]
        )
        
        logger.info(f"Report generated: {report_id} ({request.report_type.value}) by user {current_user['id']}")
        return report
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report"
        )

@router.get("/reports", response_model=List[ReportResponse])
async def list_reports(
    report_type: Optional[ReportType] = Query(None, description="Filter by report type"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    current_user: Dict = Depends(get_current_user)
):
    """
    List generated reports with filtering options.
    """
    try:
        reports = list(_mock_reports_db.values())
        
        # Filter by user access (users can only see their own reports unless admin)
        if current_user.get("role") not in ["admin", "district_admin"]:
            reports = [r for r in reports if r.generated_by == current_user["id"]]
        
        # Apply filters
        if report_type:
            reports = [r for r in reports if r.report_type == report_type]
        if status_filter:
            reports = [r for r in reports if r.status == status_filter]
        
        # Sort by generated_at descending and limit
        reports.sort(key=lambda x: x.generated_at, reverse=True)
        return reports[:limit]
        
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reports"
        )

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get specific report details.
    """
    try:
        report = _mock_reports_db.get(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Check access permissions
        if (current_user.get("role") not in ["admin", "district_admin"] and 
            report.generated_by != current_user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving report {report_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report"
        )

@router.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
@rate_limit(requests=5)  # 5 dashboard creations per minute
async def create_dashboard(
    request: DashboardConfigRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"]))
):
    """
    Create a custom analytics dashboard.
    
    Requires: Teacher or Admin role
    Rate limit: 5 requests per minute
    """
    try:
        dashboard_id = str(uuid.uuid4())
        
        # Convert widget configurations to DashboardWidget objects
        widgets = [
            DashboardWidget(
                widget_id=widget.get("widget_id", str(uuid.uuid4())),
                widget_type=widget.get("widget_type", "chart"),
                title=widget.get("title", "Untitled Widget"),
                position=widget.get("position", {"x": 0, "y": 0}),
                size=widget.get("size", {"width": 4, "height": 3}),
                configuration=widget.get("configuration", {}),
                last_updated=datetime.now(timezone.utc)
            )
            for widget in request.widgets
        ]
        
        dashboard = DashboardResponse(
            dashboard_id=dashboard_id,
            dashboard_name=request.dashboard_name,
            widgets=widgets,
            layout=request.layout,
            refresh_interval=request.refresh_interval,
            last_updated=datetime.now(timezone.utc),
            created_by=current_user["id"],
            is_default=request.is_default,
            sharing_settings=request.sharing_settings
        )
        
        # Store dashboard
        _mock_dashboards_db[dashboard_id] = dashboard
        
        # Background notification
        background_tasks.add_task(
            notify_analytics_update,
            "dashboard_created",
            {"dashboard_id": dashboard_id, "dashboard_name": request.dashboard_name, "widget_count": len(widgets)},
            current_user["id"]
        )
        
        logger.info(f"Dashboard created: {dashboard_id} ({request.dashboard_name}) by user {current_user['id']}")
        return dashboard
        
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dashboard"
        )

@router.get("/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    current_user: Dict = Depends(get_current_user)
):
    """
    List available dashboards for the current user.
    """
    try:
        dashboards = list(_mock_dashboards_db.values())
        
        # Filter by user access
        user_role = current_user.get("role")
        user_id = current_user.get("id")
        
        accessible_dashboards = []
        for dashboard in dashboards:
            # Check if user can access this dashboard
            if (dashboard.created_by == user_id or
                dashboard.is_default or
                user_role in dashboard.sharing_settings.get("roles", []) or
                user_role in ["admin", "district_admin"]):
                accessible_dashboards.append(dashboard)
        
        # Sort by is_default first, then by last_updated
        accessible_dashboards.sort(key=lambda x: (not x.is_default, x.last_updated), reverse=True)
        return accessible_dashboards
        
    except Exception as e:
        logger.error(f"Error listing dashboards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboards"
        )

@router.get("/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get specific dashboard configuration and data.
    """
    try:
        dashboard = _mock_dashboards_db.get(dashboard_id)
        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found"
            )
        
        # Check access permissions
        user_role = current_user.get("role")
        user_id = current_user.get("id")
        
        if not (dashboard.created_by == user_id or
                dashboard.is_default or
                user_role in dashboard.sharing_settings.get("roles", []) or
                user_role in ["admin", "district_admin"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Populate widget data (mock data for each widget)
        for widget in dashboard.widgets:
            if widget.widget_type == "line_chart":
                widget.data = {
                    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                    "datasets": [{
                        "label": "Engagement",
                        "data": [75, 80, 78, 85, 88]
                    }]
                }
            elif widget.widget_type == "bar_chart":
                widget.data = {
                    "labels": ["Math", "Science", "English", "History"],
                    "datasets": [{
                        "label": "Performance",
                        "data": [88, 92, 85, 79]
                    }]
                }
            else:
                widget.data = {"value": 85.5, "trend": "up"}
        
        return dashboard
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving dashboard {dashboard_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard"
        )

@router.post("/learning-analytics", response_model=LearningAnalyticsResponse)
@rate_limit(requests=20)  # 20 learning analytics requests per minute
async def analyze_learning_data(
    request: LearningAnalyticsRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"]))
):
    """
    Perform advanced learning analytics.
    
    Requires: Teacher or Admin role
    Rate limit: 20 requests per minute
    """
    try:
        analysis_id = str(uuid.uuid4())
        
        # Mock learning analytics data
        analysis = LearningAnalyticsResponse(
            analysis_id=analysis_id,
            student_performance={
                "average_score": 82.5,
                "score_distribution": {
                    "90-100": 25,
                    "80-89": 40,
                    "70-79": 25,
                    "60-69": 8,
                    "below_60": 2
                },
                "improvement_rate": 15.3,
                "mastery_levels": {
                    "mastered": 65,
                    "proficient": 25,
                    "developing": 8,
                    "beginning": 2
                }
            },
            class_performance={
                "class_average": 84.2,
                "median_score": 85.0,
                "top_performers": 15,
                "struggling_students": 8,
                "subject_averages": {
                    "mathematics": 87.5,
                    "science": 85.2,
                    "english": 82.1,
                    "history": 79.8
                }
            },
            competency_analysis={
                "problem_solving": 88.5,
                "critical_thinking": 82.3,
                "communication": 79.1,
                "collaboration": 85.7,
                "creativity": 76.9
            },
            learning_progression=[
                {
                    "week": 1,
                    "completion_rate": 78.2,
                    "average_score": 75.5,
                    "engagement_level": 82.1
                },
                {
                    "week": 2,
                    "completion_rate": 82.5,
                    "average_score": 79.3,
                    "engagement_level": 85.7
                },
                {
                    "week": 3,
                    "completion_rate": 85.1,
                    "average_score": 82.8,
                    "engagement_level": 88.2
                }
            ],
            engagement_metrics={
                "total_time_spent": 1245,  # minutes
                "average_session_duration": 25.3,
                "interaction_rate": 76.8,
                "content_completion_rate": 82.4,
                "forum_participation": 45.2
            },
            at_risk_students=[
                {
                    "student_id": "student_123",
                    "risk_factors": ["low_engagement", "declining_performance"],
                    "risk_score": 0.75,
                    "recommended_interventions": ["personalized_support", "peer_tutoring"]
                },
                {
                    "student_id": "student_456",
                    "risk_factors": ["irregular_attendance", "missed_assignments"],
                    "risk_score": 0.68,
                    "recommended_interventions": ["schedule_check_in", "assignment_reminders"]
                }
            ],
            recommendations=[
                {
                    "type": "curriculum",
                    "recommendation": "Increase interactive elements in mathematics lessons",
                    "priority": "high",
                    "expected_impact": "Improve engagement by 15%"
                },
                {
                    "type": "instruction",
                    "recommendation": "Implement peer learning groups for struggling students",
                    "priority": "medium",
                    "expected_impact": "Reduce at-risk student count by 30%"
                },
                {
                    "type": "assessment",
                    "recommendation": "Add formative assessments to identify gaps earlier",
                    "priority": "high",
                    "expected_impact": "Improve overall performance by 8%"
                }
            ],
            generated_at=datetime.now(timezone.utc)
        )
        
        # Add predictions if requested
        if request.include_predictions:
            analysis.predictions = {
                "end_of_term_performance": {
                    "predicted_average": 86.3,
                    "confidence_interval": [83.1, 89.5],
                    "students_at_risk": 6
                },
                "completion_rates": {
                    "next_week": 87.2,
                    "next_month": 84.5
                },
                "engagement_trends": {
                    "predicted_trend": "stable_with_slight_increase",
                    "factors": ["seasonal_variation", "curriculum_difficulty"]
                }
            }
        
        # Store analysis
        _mock_learning_analytics[analysis_id] = analysis
        
        # Background notification
        background_tasks.add_task(
            notify_analytics_update,
            "learning_analysis_completed",
            {"analysis_id": analysis_id, "student_count": len(request.student_ids or []), "insights_count": len(analysis.recommendations)},
            current_user["id"]
        )
        
        logger.info(f"Learning analytics completed: {analysis_id} by user {current_user['id']}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error performing learning analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform learning analytics"
        )

@router.get("/system-health", response_model=SystemHealthMetrics)
async def get_system_health(
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_role("admin"))
):
    """
    Get system health and performance metrics.
    
    Requires: Admin role
    """
    try:
        # Mock system health data
        health_metrics = SystemHealthMetrics(
            system_uptime=99.87,
            response_time_avg=145.2,
            error_rate=0.12,
            active_users=1247,
            concurrent_sessions=389,
            resource_utilization={
                "cpu_percent": 35.8,
                "memory_percent": 62.4,
                "disk_percent": 45.2,
                "network_io": 12.5
            },
            database_performance={
                "query_time_avg": 23.5,
                "connections_active": 45,
                "cache_hit_rate": 94.2,
                "slow_queries": 2
            },
            api_performance={
                "requests_per_minute": 1850,
                "success_rate": 99.88,
                "avg_response_time": 89.3,
                "rate_limit_hits": 12
            },
            recent_alerts=[
                {
                    "type": "warning",
                    "message": "High memory usage detected",
                    "timestamp": datetime.now(timezone.utc) - timedelta(minutes=15),
                    "resolved": True
                },
                {
                    "type": "info",
                    "message": "Scheduled maintenance completed",
                    "timestamp": datetime.now(timezone.utc) - timedelta(hours=2),
                    "resolved": True
                }
            ],
            timestamp=datetime.now(timezone.utc)
        )
        
        return health_metrics
        
    except Exception as e:
        logger.error(f"Error retrieving system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health metrics"
        )

@router.get("/engagement", response_model=EngagementAnalytics)
async def get_engagement_analytics(
    time_period: str = Query("7d", description="Time period: 1d, 7d, 30d, 90d"),
    current_user: Dict = Depends(get_current_user),
    _: None = Depends(require_any_role(["teacher", "admin"]))
):
    """
    Get user engagement analytics.
    
    Requires: Teacher or Admin role
    """
    try:
        # Mock engagement analytics data
        engagement_data = EngagementAnalytics(
            total_active_users=1247,
            daily_active_users=892,
            weekly_active_users=1180,
            monthly_active_users=1247,
            session_duration_avg=24.5,
            page_views_total=15680,
            feature_usage={
                "content_creation": 456,
                "roblox_integration": 234,
                "assessments": 678,
                "collaboration": 345,
                "analytics": 123
            },
            user_retention={
                "day_1": 95.2,
                "day_7": 78.5,
                "day_30": 65.8,
                "day_90": 52.3
            },
            engagement_score=82.7,
            churn_rate=8.5,
            most_popular_content=[
                {
                    "content_id": "lesson_math_001",
                    "title": "Introduction to Algebra",
                    "views": 1250,
                    "engagement_rate": 89.3
                },
                {
                    "content_id": "quiz_science_005",
                    "title": "Solar System Quiz",
                    "views": 980,
                    "engagement_rate": 92.1
                },
                {
                    "content_id": "project_history_002",
                    "title": "Ancient Civilizations",
                    "views": 756,
                    "engagement_rate": 85.7
                }
            ]
        )
        
        return engagement_data
        
    except Exception as e:
        logger.error(f"Error retrieving engagement analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engagement analytics"
        )

@router.get("/export/{query_id}")
async def export_analytics_data(
    query_id: str,
    format: str = Query("csv", description="Export format: csv, json, xlsx"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Export analytics data in various formats.
    """
    try:
        # Check if query exists in cache
        analytics_data = _mock_analytics_cache.get(query_id)
        if not analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analytics query not found or expired"
            )
        
        # Mock export functionality
        if format == "csv":
            # Would generate CSV data
            export_data = "timestamp,metric_type,value\n"
            for series in analytics_data.metric_series:
                for point in series.data_points:
                    export_data += f"{point.timestamp},{series.metric_type},{point.value}\n"
            
            return {
                "download_url": f"/api/v1/analytics/downloads/{query_id}.csv",
                "format": "csv",
                "size_bytes": len(export_data.encode('utf-8')),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
            }
        
        elif format == "json":
            return {
                "download_url": f"/api/v1/analytics/downloads/{query_id}.json",
                "format": "json",
                "size_bytes": len(analytics_data.model_dump_json().encode('utf-8')),
                "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
            }
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics data {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export analytics data"
        )
