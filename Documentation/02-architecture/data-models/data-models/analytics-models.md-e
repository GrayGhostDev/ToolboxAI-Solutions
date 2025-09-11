# Analytics and Reporting Models

This document defines the data models for analytics, reporting, and business intelligence within ToolBoxAI-Solutions.

## AnalyticsEvent Model

Raw event data captured for analytics processing.

### Schema Definition

```lua
AnalyticsEvent = {
    -- Event Identification
    id = string,                      -- Event ID (UUID)
    event_id = string,                -- Unique event identifier
    session_id = string,              -- Session identifier
    
    -- Event Details
    event = {
        name = string,                -- Event name
        category = string,            -- Event category
        action = string,              -- Specific action
        label = string,               -- Event label
        
        timestamp = DateTime,         -- Event timestamp
        
        properties = {                -- Event-specific properties
            -- Flexible key-value pairs
        },
        
        value = number,              -- Numeric value (optional)
        
        revenue = number,            -- Revenue impact (if applicable)
    },
    
    -- User Context
    user = {
        user_id = string,            -- User identifier
        anonymous_id = string,       -- Anonymous identifier
        
        role = string,               -- User role at time of event
        
        organization_id = string,    -- Organization
        
        segment = string,            -- User segment
        cohort = string,            -- User cohort
        
        attributes = {               -- User attributes at event time
            grade_level = number,
            subject = string,
            account_age_days = number,
            subscription_tier = string
        }
    },
    
    -- Context Information
    context = {
        -- Page/Screen Context
        page = {
            url = string,
            path = string,
            title = string,
            referrer = string,
            search = string          -- Query parameters
        },
        
        -- Application Context
        app = {
            name = string,
            version = string,
            build = string,
            namespace = string
        },
        
        -- Campaign Attribution
        campaign = {
            source = string,         -- utm_source
            medium = string,         -- utm_medium
            campaign = string,       -- utm_campaign
            term = string,          -- utm_term
            content = string        -- utm_content
        },
        
        -- Device Information
        device = {
            type = string,          -- "desktop", "mobile", "tablet"
            manufacturer = string,
            model = string,
            
            screen = {
                width = number,
                height = number,
                density = number
            },
            
            os = {
                name = string,
                version = string
            },
            
            browser = {
                name = string,
                version = string,
                engine = string
            }
        },
        
        -- Network Information
        network = {
            ip = string,            -- Hashed IP
            connection_type = string,
            carrier = string,
            
            location = {
                country = string,
                region = string,
                city = string,
                postal_code = string,
                timezone = string,
                coordinates = {
                    latitude = number,
                    longitude = number
                }
            }
        },
        
        -- Session Context
        session = {
            duration = number,      -- Session duration so far
            page_views = number,    -- Pages viewed in session
            events_count = number   -- Events in session
        }
    },
    
    -- Educational Context
    education = {
        course_id = string,
        lesson_id = string,
        quiz_id = string,
        
        learning_path_id = string,
        
        content_type = string,      -- Type of educational content
        interaction_type = string,  -- Type of interaction
        
        difficulty_level = string,
        
        time_on_task = number      -- Seconds on current task
    },
    
    -- Processing Metadata
    processing = {
        received_at = DateTime,     -- When event was received
        processed_at = DateTime,    -- When event was processed
        
        source = string,           -- Event source system
        
        version = string,          -- Event schema version
        
        enrichments = {string},    -- Applied enrichments
        
        quality_score = number,    -- Data quality score
        
        flags = {                  -- Processing flags
            duplicate = boolean,
            anomaly = boolean,
            test_event = boolean
        }
    }
}
```

## AggregatedMetrics Model

Pre-computed metrics for efficient reporting.

### Schema Definition

```lua
AggregatedMetrics = {
    id = string,
    
    -- Aggregation Dimensions
    dimensions = {
        time_period = string,        -- "hour", "day", "week", "month"
        start_time = DateTime,
        end_time = DateTime,
        
        granularity = string,        -- "user", "class", "school", "district"
        entity_id = string,          -- ID of entity being aggregated
        entity_type = string,        -- Type of entity
        
        segment = string,            -- User segment
        cohort = string,            -- User cohort
        
        filters = {                  -- Applied filters
            grade_level = number,
            subject = string,
            course_id = string
        }
    },
    
    -- User Metrics
    user_metrics = {
        active_users = number,       -- Unique active users
        new_users = number,          -- New registrations
        returning_users = number,    -- Returning users
        
        user_retention = {
            day_1 = number,         -- Day 1 retention %
            day_7 = number,         -- Day 7 retention %
            day_30 = number,        -- Day 30 retention %
        },
        
        churn_rate = number,        -- User churn rate
        
        average_session_duration = number,
        sessions_per_user = number,
        
        engagement_score = number   -- Calculated engagement
    },
    
    -- Learning Metrics
    learning_metrics = {
        lessons_started = number,
        lessons_completed = number,
        
        completion_rate = number,
        
        quizzes_taken = number,
        average_quiz_score = number,
        quiz_pass_rate = number,
        
        assignments_submitted = number,
        
        total_learning_time = number,  -- Total minutes
        average_learning_time = number, -- Per user
        
        content_interactions = number,
        
        skills_mastered = number,
        objectives_achieved = number,
        
        average_progress = number      -- Average progress %
    },
    
    -- Performance Metrics
    performance_metrics = {
        average_grade = number,
        grade_distribution = {
            a = number,              -- Count of A grades
            b = number,
            c = number,
            d = number,
            f = number
        },
        
        improvement_rate = number,   -- Performance improvement
        
        mastery_rate = number,       -- Concept mastery rate
        
        at_risk_students = number,   -- Students at risk
        
        intervention_success_rate = number
    },
    
    -- Engagement Metrics
    engagement_metrics = {
        login_frequency = number,
        
        content_views = number,
        content_shares = number,
        content_bookmarks = number,
        
        discussion_posts = number,
        discussion_replies = number,
        
        collaboration_sessions = number,
        
        help_requests = number,
        
        feature_adoption = {         -- Feature usage rates
            gamification = number,
            social = number,
            ai_tutor = number,
            roblox = number
        },
        
        nps_score = number          -- Net Promoter Score
    },
    
    -- Platform Metrics
    platform_metrics = {
        page_views = number,
        unique_visitors = number,
        
        api_calls = number,
        
        error_rate = number,
        
        response_time_p50 = number,  -- 50th percentile
        response_time_p95 = number,  -- 95th percentile
        response_time_p99 = number,  -- 99th percentile
        
        uptime_percentage = number,
        
        bandwidth_usage = number,    -- GB
        storage_usage = number,      -- GB
        
        compute_usage = number      -- CPU hours
    },
    
    -- Business Metrics
    business_metrics = {
        revenue = number,
        
        new_subscriptions = number,
        cancelled_subscriptions = number,
        
        mrr = number,               -- Monthly recurring revenue
        arr = number,               -- Annual recurring revenue
        
        ltv = number,               -- Lifetime value
        cac = number,               -- Customer acquisition cost
        
        conversion_rate = number,
        
        support_tickets = number,
        support_resolution_time = number
    },
    
    -- Calculated Scores
    scores = {
        health_score = number,       -- Overall health score
        risk_score = number,         -- Risk assessment
        
        quality_score = number,      -- Content quality
        
        efficiency_score = number,   -- Learning efficiency
        
        satisfaction_score = number  -- User satisfaction
    },
    
    -- Metadata
    calculated_at = DateTime,
    last_updated = DateTime,
    
    calculation_version = string,    -- Algorithm version
    
    confidence_level = number,       -- Statistical confidence
    sample_size = number,           -- Data points used
    
    anomalies_detected = {string}   -- Detected anomalies
}
```

## Dashboard Model

Configurable dashboard definitions for different user roles.

### Schema Definition

```lua
Dashboard = {
    id = string,
    name = string,
    description = string,
    
    -- Dashboard Configuration
    configuration = {
        type = string,              -- "overview", "detailed", "custom"
        
        role = string,              -- Target role
        
        layout = string,            -- "grid", "list", "tabs"
        
        refresh_interval = number,  -- Seconds between refresh
        
        time_range = {
            default = string,       -- "today", "week", "month", "custom"
            
            allow_custom = boolean,
            
            min_range = string,     -- Minimum selectable range
            max_range = string     -- Maximum selectable range
        },
        
        filters = {                 -- Available filters
            {
                name = string,
                type = string,      -- "select", "multi-select", "date", "range"
                options = {any},
                default = any
            }
        },
        
        permissions = {
            view = {string},        -- Roles that can view
            edit = {string},        -- Roles that can edit
            share = {string}       -- Roles that can share
        }
    },
    
    -- Widgets
    widgets = {
        {
            id = string,
            type = string,          -- Widget type
            -- Types: "metric", "chart", "table", "map", "timeline",
            -- "heatmap", "funnel", "gauge", "list", "text"
            
            title = string,
            description = string,
            
            position = {
                x = number,
                y = number,
                width = number,
                height = number
            },
            
            data_source = {
                type = string,      -- "metrics", "events", "custom"
                
                query = string,     -- Data query
                
                aggregation = string, -- Aggregation type
                
                dimensions = {string}, -- Group by dimensions
                
                metrics = {string}, -- Metrics to display
                
                filters = {},      -- Widget-specific filters
                
                time_range = string, -- Override dashboard range
                
                refresh = number   -- Widget refresh interval
            },
            
            visualization = {
                chart_type = string, -- For charts
                
                colors = {string},  -- Color scheme
                
                show_legend = boolean,
                show_labels = boolean,
                show_grid = boolean,
                
                axis = {
                    x_label = string,
                    y_label = string,
                    
                    x_scale = string, -- "linear", "log", "time"
                    y_scale = string
                },
                
                thresholds = {      -- Alert thresholds
                    {
                        value = number,
                        color = string,
                        label = string
                    }
                },
                
                formatting = {
                    number_format = string,
                    date_format = string,
                    
                    prefix = string,
                    suffix = string,
                    
                    decimal_places = number
                }
            },
            
            interactions = {
                clickable = boolean,
                
                drill_down = {
                    enabled = boolean,
                    target = string -- Target dashboard/report
                },
                
                export = boolean,  -- Allow export
                
                tooltips = boolean
            },
            
            conditions = {         -- Conditional formatting
                {
                    field = string,
                    operator = string,
                    value = any,
                    
                    style = {}    -- Applied style
                }
            }
        }
    },
    
    -- Alerts
    alerts = {
        {
            id = string,
            name = string,
            
            condition = {
                metric = string,
                operator = string,   -- ">", "<", "=", "change"
                threshold = number,
                
                duration = number,  -- Minutes condition must persist
                
                frequency = string  -- Check frequency
            },
            
            actions = {
                email = boolean,
                sms = boolean,
                push = boolean,
                webhook = string,
                
                recipients = {string}
            },
            
            enabled = boolean,
            
            last_triggered = DateTime,
            trigger_count = number
        }
    },
    
    -- Sharing
    sharing = {
        visibility = string,        -- "private", "team", "organization", "public"
        
        shared_with = {
            {
                entity_type = string, -- "user", "role", "group"
                entity_id = string,
                permissions = string -- "view", "edit"
            }
        },
        
        public_url = string,       -- Public share URL
        
        embed_code = string       -- Embed HTML
    },
    
    -- Schedule
    schedule = {
        enabled = boolean,
        
        frequency = string,        -- "daily", "weekly", "monthly"
        
        time = string,            -- Delivery time
        
        recipients = {
            {
                email = string,
                format = string   -- "pdf", "excel", "link"
            }
        },
        
        include_data = boolean,   -- Include raw data
        
        last_sent = DateTime,
        next_scheduled = DateTime
    },
    
    -- Metadata
    owner_id = string,
    
    created_at = DateTime,
    updated_at = DateTime,
    
    last_viewed = DateTime,
    view_count = number,
    
    tags = {string},
    
    version = number,
    
    is_default = boolean,         -- Default for role
    is_template = boolean        -- Template dashboard
}
```

## Report Model

Structured reports for detailed analysis and compliance.

### Schema Definition

```lua
Report = {
    id = string,
    title = string,
    description = string,
    
    -- Report Type
    type = string,                 -- Report type
    -- Types: "progress", "performance", "engagement", "compliance",
    -- "financial", "usage", "custom"
    
    category = string,             -- Report category
    
    -- Report Configuration
    configuration = {
        format = string,           -- "pdf", "excel", "html", "csv"
        
        template = string,         -- Report template
        
        sections = {               -- Report sections
            {
                name = string,
                type = string,     -- "summary", "detail", "chart", "table"
                
                content = {
                    title = string,
                    description = string,
                    
                    data_source = string,
                    
                    query = string,
                    
                    visualization = string,
                    
                    include_raw_data = boolean
                },
                
                order = number,
                
                page_break = boolean -- Force page break after
            }
        },
        
        parameters = {             -- Report parameters
            {
                name = string,
                type = string,
                required = boolean,
                default = any,
                
                validation = {}
            }
        },
        
        filters = {               -- Applied filters
            date_range = {
                start = DateTime,
                end = DateTime
            },
            
            entities = {string},  -- Entity IDs
            
            custom = {}          -- Custom filters
        },
        
        grouping = {             -- Data grouping
            group_by = {string},
            
            subtotals = boolean,
            
            grand_total = boolean
        },
        
        sorting = {
            field = string,
            direction = string   -- "asc", "desc"
        },
        
        formatting = {
            logo_url = string,
            
            header = string,     -- Report header
            footer = string,     -- Report footer
            
            styles = {},        -- CSS/formatting styles
            
            charts = {
                theme = string,
                colors = {string}
            },
            
            tables = {
                striped = boolean,
                borders = boolean,
                compact = boolean
            }
        }
    },
    
    -- Data
    data = {
        generated_at = DateTime,
        
        period = {
            start = DateTime,
            end = DateTime
        },
        
        summary = {              -- Summary statistics
            -- Key metrics
        },
        
        details = {             -- Detailed data
            -- Report content
        },
        
        charts = {              -- Chart data
            {
                id = string,
                type = string,
                data = {},
                config = {}
            }
        },
        
        tables = {              -- Table data
            {
                id = string,
                headers = {string},
                rows = {{any}},
                totals = {any}
            }
        },
        
        metadata = {
            row_count = number,
            
            processing_time = number,
            
            data_quality = number,
            
            warnings = {string},
            
            notes = string
        }
    },
    
    -- Distribution
    distribution = {
        recipients = {
            {
                type = string,   -- "user", "email", "webhook"
                
                destination = string,
                
                format = string,
                
                delivered = boolean,
                delivered_at = DateTime,
                
                opened = boolean,
                opened_at = DateTime
            }
        },
        
        schedule = {
            frequency = string,
            
            next_run = DateTime,
            
            active = boolean
        },
        
        retention = {
            days = number,       -- Days to retain
            
            archive = boolean,   -- Archive after retention
            
            delete_after = DateTime
        }
    },
    
    -- Compliance
    compliance = {
        regulation = string,     -- "ferpa", "coppa", "gdpr"
        
        data_classification = string,
        
        audit_trail = {
            {
                action = string,
                user_id = string,
                timestamp = DateTime,
                ip_address = string
            }
        },
        
        redactions = {          -- Redacted fields
            {
                field = string,
                reason = string
            }
        },
        
        certifications = {
            certified_by = string,
            certified_at = DateTime,
            
            signature = string
        }
    },
    
    -- Status
    status = string,            -- "draft", "generating", "ready", "sent", "archived"
    
    generation_time = number,   -- Seconds to generate
    
    file_size = number,        -- Bytes
    
    file_url = string,         -- Download URL
    
    expires_at = DateTime,     -- URL expiration
    
    -- Metadata
    created_by = string,
    created_at = DateTime,
    
    last_accessed = DateTime,
    access_count = number,
    
    tags = {string},
    
    version = number
}
```

## InsightModel

AI-generated insights and recommendations.

### Schema Definition

```lua
Insight = {
    id = string,
    
    -- Insight Details
    type = string,              -- Insight type
    -- Types: "trend", "anomaly", "prediction", "recommendation",
    -- "correlation", "pattern", "alert"
    
    category = string,          -- Category
    
    title = string,
    description = string,
    
    summary = string,          -- Brief summary
    
    -- Analysis
    analysis = {
        metric = string,       -- Primary metric
        
        dimension = string,    -- Analysis dimension
        
        segment = string,      -- Analyzed segment
        
        time_period = {
            start = DateTime,
            end = DateTime
        },
        
        data_points = number,  -- Data points analyzed
        
        statistical = {
            mean = number,
            median = number,
            std_dev = number,
            
            trend = string,    -- "increasing", "decreasing", "stable"
            
            change_rate = number,
            
            correlation = number,
            
            confidence = number,
            
            p_value = number
        },
        
        comparison = {
            baseline = number,
            current = number,
            
            change = number,
            change_percentage = number,
            
            vs_average = number,
            vs_best = number
        },
        
        factors = {            -- Contributing factors
            {
                factor = string,
                impact = number,
                confidence = number
            }
        }
    },
    
    -- Visualization
    visualization = {
        type = string,         -- Chart type
        
        data = {},            -- Chart data
        
        highlights = {        -- Data points to highlight
            {
                point = any,
                label = string,
                color = string
            }
        },
        
        annotations = {       -- Chart annotations
            {
                type = string,
                position = {},
                text = string
            }
        }
    },
    
    -- Impact
    impact = {
        severity = string,     -- "low", "medium", "high", "critical"
        
        urgency = string,     -- "low", "medium", "high", "immediate"
        
        affected_users = number,
        
        affected_areas = {string},
        
        potential_value = number, -- Potential value/cost
        
        risk_score = number
    },
    
    -- Recommendations
    recommendations = {
        {
            action = string,
            
            description = string,
            
            priority = number,
            
            effort = string,   -- "low", "medium", "high"
            
            expected_impact = number,
            
            resources = {string},
            
            timeline = string
        }
    },
    
    -- Related Insights
    related = {
        insights = {string},   -- Related insight IDs
        
        reports = {string},   -- Related report IDs
        
        dashboards = {string} -- Related dashboard IDs
    },
    
    -- Feedback
    feedback = {
        useful = boolean,
        
        rating = number,
        
        comments = string,
        
        action_taken = string,
        
        outcome = string
    },
    
    -- Status
    status = string,          -- "new", "reviewed", "actioned", "dismissed"
    
    reviewed_by = string,
    reviewed_at = DateTime,
    
    -- AI Generation
    ai = {
        model = string,       -- AI model used
        
        version = string,     -- Model version
        
        prompt = string,      -- Generation prompt
        
        parameters = {},     -- Model parameters
        
        processing_time = number,
        
        cost = number        -- Generation cost
    },
    
    -- Metadata
    generated_at = DateTime,
    
    expires_at = DateTime,    -- When insight expires
    
    tags = {string},
    
    priority = number,
    
    auto_generated = boolean
}
```

## Implementation Notes

### Event Processing Pipeline

```python
class AnalyticsPipeline:
    async def process_event(self, event: AnalyticsEvent):
        # 1. Validation
        validated = await self.validate_event(event)
        
        # 2. Enrichment
        enriched = await self.enrich_event(validated)
        
        # 3. Stream Processing
        await self.stream_processor.process(enriched)
        
        # 4. Batch Aggregation
        await self.batch_aggregator.add(enriched)
        
        # 5. Real-time Updates
        await self.update_real_time_metrics(enriched)
        
        # 6. Anomaly Detection
        await self.detect_anomalies(enriched)
        
        # 7. Trigger Insights
        await self.generate_insights(enriched)
```

### Metric Aggregation Strategy

```lua
AggregationStrategy = {
    dimensions = {
        time = {"minute", "hour", "day", "week", "month"},
        
        entity = {"user", "class", "school", "district"},
        
        content = {"lesson", "course", "subject"}
    },
    
    metrics = {
        count = "COUNT(*)",
        
        unique = "COUNT(DISTINCT user_id)",
        
        average = "AVG(value)",
        
        percentile = "PERCENTILE_CONT(0.5)",
        
        sum = "SUM(value)"
    },
    
    windows = {
        tumbling = {           -- Fixed windows
            size = "1 hour",
            
            overlap = 0
        },
        
        sliding = {           -- Overlapping windows
            size = "1 hour",
            
            slide = "15 minutes"
        },
        
        session = {          -- Session-based windows
            gap = "30 minutes"
        }
    },
    
    storage = {
        hot = "7 days",      -- Recent data in fast storage
        
        warm = "90 days",    -- Older data in slower storage
        
        cold = "2 years"     -- Archive storage
    }
}
```

### Dashboard Performance Optimization

```python
class DashboardOptimizer:
    def optimize_queries(self, dashboard: Dashboard):
        # Identify common filters
        common_filters = self.extract_common_filters(dashboard.widgets)
        
        # Create materialized views
        for filter_set in common_filters:
            self.create_materialized_view(filter_set)
        
        # Implement query caching
        cache_keys = self.generate_cache_keys(dashboard.widgets)
        
        # Pre-compute expensive aggregations
        self.precompute_aggregations(dashboard)
        
        # Optimize widget refresh
        self.batch_widget_refreshes(dashboard.widgets)
```

### Insight Generation

```python
class InsightGenerator:
    async def generate_insights(self, metrics: AggregatedMetrics):
        insights = []
        
        # Trend Detection
        if trend := self.detect_trend(metrics):
            insights.append(self.create_trend_insight(trend))
        
        # Anomaly Detection
        if anomaly := self.detect_anomaly(metrics):
            insights.append(self.create_anomaly_insight(anomaly))
        
        # Pattern Recognition
        if pattern := self.find_pattern(metrics):
            insights.append(self.create_pattern_insight(pattern))
        
        # Predictive Analysis
        if prediction := self.predict_future(metrics):
            insights.append(self.create_prediction_insight(prediction))
        
        # Recommendations
        recommendations = self.generate_recommendations(metrics)
        insights.extend(recommendations)
        
        return insights
```

### Real-time Analytics

```lua
RealTimeAnalytics = {
    streaming = {
        platform = "Apache Kafka",
        
        topics = {
            events = "analytics.events",
            metrics = "analytics.metrics",
            alerts = "analytics.alerts"
        },
        
        processing = "Apache Flink"
    },
    
    websocket = {
        channels = {
            dashboard = "/ws/dashboard/{dashboard_id}",
            
            metrics = "/ws/metrics/{metric_name}",
            
            alerts = "/ws/alerts/{user_id}"
        },
        
        update_frequency = 1000  -- Milliseconds
    },
    
    cache = {
        provider = "Redis",
        
        ttl = {
            real_time = 10,      -- Seconds
            
            aggregated = 300,    -- 5 minutes
            
            reports = 3600      -- 1 hour
        }
    }
}
```

---

*For user activity tracking, see [Progress Models](progress-models.md). For assessment analytics, see [Quiz Models](quiz-models.md).*