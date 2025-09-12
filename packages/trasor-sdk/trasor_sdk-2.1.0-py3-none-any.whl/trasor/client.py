"""
Trasor.io Python SDK Client with unified async support

This implementation provides a single client that can operate in both
sync and async modes based on initialization parameter.
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from .exceptions import AuthenticationError, ValidationError, APIError, TrasorError


class TrasorClient:
    """
    Client for interacting with the Trasor.io API.
    
    Supports both synchronous and asynchronous operation modes.
    
    Example (sync mode):
        client = TrasorClient(api_key="trasor_live_xxx")
        response = client.log_event(agent_name="agent", action="action")
        
    Example (async mode):
        import asyncio
        
        async def main():
            client = TrasorClient(api_key="trasor_live_xxx", async_mode=True)
            response = await client.log_event(agent_name="agent", action="action")
            
        asyncio.run(main())
    """
    
    def __init__(
        self, 
        api_key: str, 
        base_url: str = "https://api.trasor.io/v1",
        timeout: int = 30,
        async_mode: bool = False
    ):
        """
        Initialize the Trasor.io client.
        
        Args:
            api_key: Your Trasor.io API key
            base_url: Base URL for the API (default: https://api.trasor.io/v1)
            timeout: Request timeout in seconds (default: 30)
            async_mode: Enable async operation mode (default: False)
            
        Raises:
            ValueError: If api_key is empty or invalid format
        """
        if not api_key:
            raise ValueError("API key is required")
            
        if not isinstance(api_key, str):
            raise ValueError("API key must be a string")
            
        if not api_key.startswith("trasor_"):
            raise ValueError("Invalid API key format")
            
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.async_mode = async_mode
        
        # Set up appropriate session based on mode
        if self.async_mode:
            self._session = None  # Will be created on first use
        else:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Trasor.io-Python-SDK/2.0.0"
            })
    
    def __enter__(self):
        """Context manager entry for sync mode."""
        if self.async_mode:
            raise RuntimeError("Use 'async with' for async mode")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for sync mode."""
        if hasattr(self, '_session') and self._session:
            self._session.close()
            
    async def __aenter__(self):
        """Context manager entry for async mode."""
        if not self.async_mode:
            raise RuntimeError("Use 'with' for sync mode")
        await self._ensure_async_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for async mode."""
        if self._session and not self._session.closed:
            await self._session.close()
            
    async def _ensure_async_session(self):
        """Ensure aiohttp session exists for async mode."""
        if self._session is None or self._session.closed:
            try:
                import aiohttp
            except ImportError:
                raise ImportError(
                    "aiohttp is required for async mode. "
                    "Install with: pip install trasor-sdk[async]"
                )
            
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Trasor.io-Python-SDK/2.0.0"
                }
            )
            
    def _sync_request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict:
        """Make a synchronous HTTP request."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json_data,
                timeout=self.timeout
            )
            
            # Parse response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"message": response.text}
                
            # Handle status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    response_data.get("message", "Invalid or missing API key")
                )
            elif response.status_code == 400:
                raise ValidationError(
                    response_data.get("message", "Invalid request data")
                )
            elif response.status_code == 429:
                raise APIError(
                    response_data.get("message", "Rate limit exceeded")
                )
            elif response.status_code >= 500:
                raise APIError(
                    f"Server error: {response.status_code} - {response_data.get('message', 'Unknown error')}"
                )
            elif response.status_code >= 400:
                raise APIError(
                    f"Client error: {response.status_code} - {response_data.get('message', 'Unknown error')}"
                )
                
            return response_data
            
        except Exception as e:
            if isinstance(e, (AuthenticationError, ValidationError, APIError)):
                raise
            raise TrasorError(f"Request failed: {str(e)}")
            
    async def _async_request(self, method: str, endpoint: str, json_data: Optional[Dict] = None) -> Dict:
        """Make an asynchronous HTTP request."""
        await self._ensure_async_session()
        
        url = urljoin(self.base_url, endpoint)
        
        try:
            async with self._session.request(method, url, json=json_data) as response:
                response_text = await response.text()
                
                # Parse response
                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {"message": response_text}
                
                # Handle status codes
                if response.status == 401:
                    raise AuthenticationError(
                        response_data.get("message", "Invalid or missing API key")
                    )
                elif response.status == 400:
                    raise ValidationError(
                        response_data.get("message", "Invalid request data")
                    )
                elif response.status == 429:
                    raise APIError(
                        response_data.get("message", "Rate limit exceeded")
                    )
                elif response.status >= 500:
                    raise APIError(
                        f"Server error: {response.status} - {response_data.get('message', 'Unknown error')}"
                    )
                elif response.status >= 400:
                    raise APIError(
                        f"Client error: {response.status} - {response_data.get('message', 'Unknown error')}"
                    )
                    
                return response_data
                
        except Exception as e:
            if isinstance(e, (AuthenticationError, ValidationError, APIError)):
                raise
            raise TrasorError(f"Request failed: {str(e)}")
            
    def _request(self, method: str, endpoint: str, json_data: Optional[Dict] = None):
        """Route request to sync or async implementation based on mode."""
        if self.async_mode:
            return self._async_request(method, endpoint, json_data)
        else:
            return self._sync_request(method, endpoint, json_data)
            
    def log_event(
        self,
        agent_name: str,
        action: str,
        inputs: Optional[Dict] = None,
        outputs: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None
    ):
        """
        Log a single audit event.
        
        In async mode, this method returns a coroutine that must be awaited.
        
        Args:
            agent_name: Name of the agent performing the action
            action: Action being performed
            inputs: Optional input data
            outputs: Optional output data
            metadata: Optional metadata
            workflow_id: Optional workflow identifier
            status: Optional status (e.g., "success", "error")
            
        Returns:
            dict: The created log entry (or coroutine in async mode)
            
        Example (sync):
            response = client.log_event("agent", "action")
            
        Example (async):
            response = await client.log_event("agent", "action")
        """
        # Validate required parameters
        if not agent_name or not isinstance(agent_name, str):
            raise ValidationError("agent_name is required and must be a string")
            
        if not action or not isinstance(action, str):
            raise ValidationError("action is required and must be a string")
            
        # Validate optional parameters
        if inputs is not None and not isinstance(inputs, dict):
            raise ValidationError("inputs must be a dictionary")
            
        if outputs is not None and not isinstance(outputs, dict):
            raise ValidationError("outputs must be a dictionary")
            
        if metadata is not None and not isinstance(metadata, dict):
            raise ValidationError("metadata must be a dictionary")
            
        if workflow_id is not None and not isinstance(workflow_id, str):
            raise ValidationError("workflow_id must be a string")
            
        if status is not None and not isinstance(status, str):
            raise ValidationError("status must be a string")
            
        # Build payload
        payload = {
            "agent_name": agent_name,
            "action": action
        }
        
        if inputs is not None:
            payload["inputs"] = inputs
        if outputs is not None:
            payload["outputs"] = outputs
        if metadata is not None:
            payload["metadata"] = metadata
        if workflow_id is not None:
            payload["workflow_id"] = workflow_id
        if status is not None:
            payload["status"] = status
            
        return self._request("POST", "/logs", payload)
        
    def log_batch(self, events: List[Dict[str, Any]]):
        """
        Log multiple audit events in a single batch request.
        
        In async mode, this method returns a coroutine that must be awaited.
        
        Args:
            events: List of event dictionaries, each containing:
                - agent_name (required): Name of the agent
                - action (required): Action performed
                - inputs (optional): Input data
                - outputs (optional): Output data
                - metadata (optional): Additional metadata
                - workflow_id (optional): Workflow identifier
                - status (optional): Status of the action
                
        Returns:
            dict: Response containing the created log entries
            
        Example:
            batch = [
                {"agent_name": "agent1", "action": "action1"},
                {"agent_name": "agent2", "action": "action2"}
            ]
            response = client.log_batch(batch)  # or await client.log_batch(batch)
        """
        # Validate events parameter
        if not isinstance(events, list):
            raise ValidationError("events must be a list")
            
        if not events:
            raise ValidationError("events list cannot be empty")
            
        # Validate each event
        for i, event in enumerate(events):
            if not isinstance(event, dict):
                raise ValidationError(f"Event at index {i} must be a dictionary")
                
            # Check required fields
            if "agent_name" not in event:
                raise ValidationError(f"Event at index {i} missing required field: agent_name")
            if "action" not in event:
                raise ValidationError(f"Event at index {i} missing required field: action")
                
            # Validate field types
            if not isinstance(event["agent_name"], str):
                raise ValidationError(f"Event at index {i}: agent_name must be a string")
            if not isinstance(event["action"], str):
                raise ValidationError(f"Event at index {i}: action must be a string")
                
            # Validate optional fields
            if "inputs" in event and not isinstance(event["inputs"], dict):
                raise ValidationError(f"Event at index {i}: inputs must be a dictionary")
            if "outputs" in event and not isinstance(event["outputs"], dict):
                raise ValidationError(f"Event at index {i}: outputs must be a dictionary")
            if "metadata" in event and not isinstance(event["metadata"], dict):
                raise ValidationError(f"Event at index {i}: metadata must be a dictionary")
            if "workflow_id" in event and not isinstance(event["workflow_id"], str):
                raise ValidationError(f"Event at index {i}: workflow_id must be a string")
            if "status" in event and not isinstance(event["status"], str):
                raise ValidationError(f"Event at index {i}: status must be a string")
                
        # Send batch request
        return self._request("POST", "/logs", events)
        
    def get_logs(self, limit: int = 50, offset: int = 0):
        """
        Retrieve audit logs with pagination.
        
        In async mode, this method returns a coroutine that must be awaited.
        
        Args:
            limit: Maximum number of logs to return (default: 50, max: 100)
            offset: Number of logs to skip (default: 0)
            
        Returns:
            dict: Logs array and pagination info
        """
        if not isinstance(limit, int) or limit < 1:
            raise ValidationError("limit must be a positive integer")
        if not isinstance(offset, int) or offset < 0:
            raise ValidationError("offset must be a non-negative integer")
            
        return self._request("GET", f"/logs?limit={limit}&offset={offset}")
        
    def verify_chain(self):
        """
        Verify the integrity of the audit log chain.
        
        In async mode, this method returns a coroutine that must be awaited.
        
        Returns:
            dict: Verification status and details
        """
        return self._request("GET", "/verify")
        
    def get_stats(self):
        """
        Get account statistics and system health.
        
        In async mode, this method returns a coroutine that must be awaited.
        
        Returns:
            dict: Account statistics
        """
        return self._request("GET", "/stats")
    
    # ===== New Security Features =====
    
    def generate_zk_proof(self, agent_name: str, start_date: str = None, end_date: str = None):
        """
        Generate a Zero-Knowledge proof for audit logs.
        
        Args:
            agent_name: Name of the agent to generate proof for
            start_date: Start date for proof generation (ISO format)
            end_date: End date for proof generation (ISO format)
            
        Returns:
            dict: ZK proof data including merkle root and proof hash
        """
        params = {"agent": agent_name}
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date
            
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        return self._request("GET", f"/zk-proof/generate?{query}")
    
    def verify_zk_proof(self, proof_hash: str):
        """
        Verify a Zero-Knowledge proof.
        
        Args:
            proof_hash: Hash of the proof to verify
            
        Returns:
            dict: Verification result
        """
        return self._request("GET", f"/zk-proof/verify/{proof_hash}")
    
    def get_drift_alerts(self, agent_name: str = None, severity: str = None):
        """
        Get behavioral drift alerts for agents.
        
        Args:
            agent_name: Filter by specific agent (optional)
            severity: Filter by severity level (critical, high, medium, low)
            
        Returns:
            list: Drift alerts and anomalies
        """
        params = {}
        if agent_name:
            params["agent"] = agent_name
        if severity:
            params["severity"] = severity
            
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/drift/alerts?{query}" if params else "/drift/alerts"
        return self._request("GET", endpoint)
    
    def set_agent_baseline(self, agent_name: str, metrics: dict):
        """
        Set behavioral baseline for an agent.
        
        Args:
            agent_name: Name of the agent
            metrics: Baseline metrics (e.g., average_response_time, error_rate)
            
        Returns:
            dict: Baseline configuration status
        """
        return self._request("POST", f"/agents/{agent_name}/baseline", metrics)
    
    def assign_agent_role(self, agent_name: str, role_id: int, enforcement_mode: str = "monitor_only"):
        """
        Assign an RBAC role to an agent.
        
        Args:
            agent_name: Name of the agent
            role_id: ID of the role to assign
            enforcement_mode: One of "monitor_only", "block_violations", "alert_and_block"
            
        Returns:
            dict: Role assignment status
        """
        data = {
            "roleId": role_id,
            "enforcementMode": enforcement_mode
        }
        return self._request("POST", f"/agents/{agent_name}/role", data)
    
    def get_rbac_violations(self, limit: int = 100):
        """
        Get recent RBAC permission violations.
        
        Args:
            limit: Maximum number of violations to return
            
        Returns:
            list: Recent permission violations
        """
        return self._request("GET", f"/rbac/violations?limit={limit}")
    
    def get_iso_compliance_score(self):
        """
        Get ISO 42001 compliance score and breakdown.
        
        Returns:
            dict: Compliance score by category
        """
        return self._request("GET", "/iso-compliance/score")
    
    def get_threat_analysis(self, time_range: str = "24h"):
        """
        Get threat analysis and security recommendations.
        
        Args:
            time_range: Time range for analysis (e.g., "1h", "24h", "7d")
            
        Returns:
            dict: Threat analysis including patterns and recommendations
        """
        return self._request("GET", f"/threat-monitoring/analysis?range={time_range}")
    
    def get_observability_metrics(self, agent_name: str = None, metric_type: str = None):
        """
        Get real-time observability metrics.
        
        Args:
            agent_name: Filter by specific agent (optional)
            metric_type: Type of metrics (performance, errors, activity)
            
        Returns:
            dict: Observability metrics and timeseries data
        """
        params = {}
        if agent_name:
            params["agent"] = agent_name
        if metric_type:
            params["type"] = metric_type
            
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        endpoint = f"/observability/metrics?{query}" if params else "/observability/metrics"
        return self._request("GET", endpoint)
        
    def close(self):
        """
        Close the client session.
        
        For sync mode, closes immediately.
        For async mode, returns a coroutine that must be awaited.
        """
        if self.async_mode:
            async def _close():
                if self._session and not self._session.closed:
                    await self._session.close()
            return _close()
        else:
            if hasattr(self, '_session') and self._session:
                self._session.close()