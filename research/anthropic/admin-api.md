# Admin & Usage APIs

Programmatic management of organization resources, usage tracking, and cost monitoring.

## Admin API

Programmatically manage organization resources including members, workspaces, and API keys.

### Authentication

Requires Admin API key (starts with `sk-ant-admin...`):
- Only admins can provision Admin API keys
- Created through Claude Console
- Different from standard API keys

### Workspace Management

```python
import anthropic

admin_client = anthropic.Anthropic(
    api_key="sk-ant-admin-..."
)

# List workspaces
workspaces = admin_client.admin.workspaces.list()

# Create workspace
workspace = admin_client.admin.workspaces.create(
    name="Production",
    description="Production API workspace"
)

# Set spending limit
admin_client.admin.workspaces.update(
    workspace_id=workspace.id,
    spending_limit_usd=1000
)
```

### Member Management

```python
# List members
members = admin_client.admin.members.list()

# Invite member
admin_client.admin.members.create(
    email="developer@example.com",
    role="developer"
)

# Update role
admin_client.admin.members.update(
    member_id="member_123",
    role="admin"
)
```

### API Key Management

```python
# List API keys
keys = admin_client.admin.api_keys.list(workspace_id="ws_123")

# Create API key
key = admin_client.admin.api_keys.create(
    workspace_id="ws_123",
    name="Production Key"
)

# Revoke key
admin_client.admin.api_keys.delete(key_id="key_123")
```

## Usage & Cost API

Programmatic access to historical API usage and cost data.

### Key Features

- Precise token counts
- Cost reconciliation for finance teams
- Product performance monitoring
- Rate limit optimization

### Basic Usage

```python
# Get usage data
usage = admin_client.admin.usage.list(
    start_date="2025-01-01",
    end_date="2025-01-31",
    workspace_id="ws_123"
)

for record in usage.data:
    print(f"Date: {record.date}")
    print(f"Model: {record.model}")
    print(f"Input tokens: {record.input_tokens}")
    print(f"Output tokens: {record.output_tokens}")
    print(f"Cost: ${record.cost_usd}")
```

### Filtering Options

```python
usage = admin_client.admin.usage.list(
    start_date="2025-01-01",
    end_date="2025-01-31",
    workspace_id="ws_123",
    model="claude-sonnet-4-5-20250929",
    group_by="day"  # or "hour", "model", "api_key"
)
```

## Claude Code Analytics API

Detailed productivity metrics for Claude Code usage.

### Available Metrics

| Category | Metrics |
|----------|---------|
| Sessions | Total sessions, duration |
| Code | Lines generated, languages |
| Git | Commits, pull requests |
| Tools | Edit/Write/Bash usage |
| Cost | Tokens, estimated cost |

### Usage

```python
analytics = admin_client.admin.claude_code_analytics.list(
    start_date="2025-01-01",
    end_date="2025-01-31",
    group_by="user"
)

for user in analytics.data:
    print(f"User: {user.user_id}")
    print(f"Sessions: {user.session_count}")
    print(f"Lines of code: {user.lines_of_code}")
    print(f"Tool acceptance rate: {user.tool_acceptance_rate}%")
```

### Tool Usage Analysis

```python
# Monitor tool acceptance/rejection
tool_stats = admin_client.admin.claude_code_analytics.tools(
    start_date="2025-01-01",
    end_date="2025-01-31"
)

for tool in tool_stats.data:
    print(f"Tool: {tool.name}")
    print(f"Accepted: {tool.accepted_count}")
    print(f"Rejected: {tool.rejected_count}")
    print(f"Acceptance rate: {tool.acceptance_rate}%")
```

## Third-Party Integrations

### Grafana Cloud

```yaml
# grafana-cloud-config.yaml
integrations:
  anthropic:
    api_key: sk-ant-admin-...
    metrics:
      - usage
      - cost
      - latency
```

**Features:**
- Pre-built dashboard
- Automatic alerts
- No additional agents required

### Datadog

```python
# Datadog integration
from datadog import initialize, statsd

options = {
    'statsd_host': '127.0.0.1',
    'statsd_port': 8125,
}
initialize(**options)

# Metrics automatically collected via Cloud Cost Management
```

### Honeycomb

Uses OpenTelemetry receiver for structured telemetry:

```yaml
receivers:
  anthropic:
    api_key: ${ANTHROPIC_ADMIN_KEY}
    poll_interval: 60s
```

## Console Features

### Workspace Architecture (Jan 2025)

- Isolated environments per workspace
- Independent API keys per workspace
- Custom spending limits per project
- Granular team access controls

### Dashboard Capabilities

| Feature | Description |
|---------|-------------|
| Real-time usage | Current day statistics |
| Historical trends | 30/60/90 day views |
| Cost breakdown | By model, workspace, API key |
| Rate limit monitoring | Current vs. limits |

### Custom Reports

Build executive dashboards with:
- Token usage trends
- Cost allocation
- Team productivity
- Model performance comparison

## Rate Limits

| Tier | Requests/min | Tokens/min |
|------|--------------|------------|
| Free | 60 | 40k |
| Build | 1,000 | 80k |
| Scale | 4,000 | 400k |
| Enterprise | Custom | Custom |

### Monitoring Rate Limits

```python
response = client.messages.create(...)

# Check headers
remaining = response.headers.get("x-ratelimit-remaining-requests")
reset_time = response.headers.get("x-ratelimit-reset-requests")
```

## Best Practices

1. **Create separate workspaces** for prod/staging/dev
2. **Set spending limits** per workspace
3. **Monitor usage daily** during initial rollout
4. **Use rate limit headers** for proactive throttling
5. **Integrate with observability** platforms early

## References

- [Admin API Documentation](https://console.anthropic.com/docs/en/build-with-claude/administration-api)
- [Usage & Cost API](https://platform.claude.com/docs/en/build-with-claude/usage-cost-api)
- [Claude Code Analytics](https://docs.anthropic.com/en/api/claude-code-analytics-api)
- [Console Guide](https://support.anthropic.com/en/articles/9534590-cost-and-usage-reporting-in-console)
