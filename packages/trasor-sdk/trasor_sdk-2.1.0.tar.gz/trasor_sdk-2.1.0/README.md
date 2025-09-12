# Trasor Python SDK

Official Python SDK for [Trasor.io](https://trasor.io) - AI Agent Security & Governance Platform

## Installation

```bash
pip install trasor-sdk
```

## Quick Start

```python
from trasor import TrasorClient

# Initialize the client
client = TrasorClient(api_key="trasor_live_your_api_key_here")

# Log an audit event
result = client.log_event(
    agent_name="my_agent",
    action="process_data",
    inputs={"user_id": "12345", "query": "Hello world"},
    outputs={"response": "Hello! How can I help you?"},
    status="success"
)

print(f"Event logged: {result['id']}")
```

## Security & Governance Features

### Zero-Knowledge Proofs
Generate cryptographic proofs for audit verification without exposing sensitive data:

```python
# Generate proof
proof = client.generate_zk_proof(
    agent_name="payment_processor",
    start_date="2025-01-01", 
    end_date="2025-01-31"
)

# Verify proof
verification = client.verify_zk_proof(proof["hash"])
```

### Behavioral Drift Detection
Monitor agent behavior and detect anomalies:

```python
# Set baseline behavior
client.set_agent_baseline("my_agent", {
    "average_response_time": 150,
    "error_rate": 0.01,
    "normal_actions": ["process_payment", "validate_card"]
})

# Get drift alerts
alerts = client.get_drift_alerts(
    agent_name="my_agent",
    severity="critical"
)
```

### Role-Based Access Control (RBAC)
Manage agent permissions and monitor violations:

```python
# Assign role to agent
client.assign_agent_role(
    agent_name="data_processor",
    role_id=2,  # Writer role
    enforcement_mode="block_violations"
)

# Monitor violations
violations = client.get_rbac_violations(limit=50)
```

### Compliance & Monitoring
Track ISO 42001 compliance and security threats:

```python
# Get compliance score
compliance = client.get_iso_compliance_score()
print(f"Overall Score: {compliance['overallScore']}%")

# Analyze security threats
threats = client.get_threat_analysis(time_range="24h")

# Get real-time metrics
metrics = client.get_observability_metrics(
    agent_name="my_agent",
    metric_type="performance"
)
```

## Framework Integrations

### CrewAI Integration
```python
from trasor.integrations.crewai import TrasorCrewCallbacks

crew = Crew(
    agents=[agent],
    tasks=[task],
    callbacks=[TrasorCrewCallbacks(api_key="trasor_live_xxx")]
)
```

### LangChain Integration
```python
from trasor.integrations.langchain import TrasorLangChainCallback
from langchain.callbacks import CallbackManager

callback_manager = CallbackManager([
    TrasorLangChainCallback(api_key="trasor_live_xxx")
])
```

## API Reference

For complete API documentation, visit: https://docs.trasor.io/api

## Support

- Documentation: https://docs.trasor.io
- Email: support@trasor.io
- GitHub Issues: https://github.com/trasor-io/trasor-python/issues

## License

MIT License. See LICENSE file for details.