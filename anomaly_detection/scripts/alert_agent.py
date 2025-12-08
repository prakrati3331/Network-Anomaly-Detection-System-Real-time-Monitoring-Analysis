"""
Alert Agent - Handles generation and sending of anomaly alerts with rate limiting
"""

import os
import time
from collections import defaultdict
from openai import OpenAI
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

class AlertAgent:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model: str = "openai/gpt-3.5-turbo",
                 base_url: str = "https://openrouter.ai/api/v1",
                 rate_limit: int = 5,  # Max alerts per minute
                 cooldown: int = 300,  # 5 minutes cooldown for same alert type
                 alert_history_size: int = 1000):  # Max alerts to keep in history
        """
        Initialize the Alert Agent with rate limiting and alert history
        
        Args:
            api_key: Your OpenRouter API key. If not provided, will look for OPENAI_API_KEY in environment.
            model: Model to use for generating alerts (e.g., 'openai/gpt-3.5-turbo')
            base_url: Base URL for the API (defaults to OpenRouter)
            rate_limit: Maximum number of alerts allowed per minute
            cooldown: Cooldown period in seconds for the same alert type
            alert_history_size: Maximum number of alerts to keep in history
        """
        self.model = model
        self.rate_limit = rate_limit
        self.cooldown = cooldown
        self.alert_history = defaultdict(list)
        self.alert_cooldowns = {}
        self.alert_history_size = alert_history_size
        
        # Initialize OpenAI client if API key is available
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(
                base_url=base_url,
                api_key=api_key,
                default_headers={
                    "HTTP-Referer": "https://github.com/yourusername/anomaly-detection",
                    "X-Title": "Anomaly Detection System"
                }
            )
        else:
            self.client = None
            print("⚠️  No API key provided. Alert message generation will be limited.")
    
    def _is_rate_limited(self, alert_type: str) -> bool:
        """
        Check if an alert should be rate limited
        
        Args:
            alert_type: Type of alert (e.g., 'high', 'medium', 'low')
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        now = time.time()
        
        # Remove old entries (older than 1 minute)
        self.alert_history[alert_type] = [
            t for t in self.alert_history[alert_type] 
            if now - t < 60
        ]
        
        # Check cooldown for this alert type
        last_alert = self.alert_cooldowns.get(alert_type, 0)
        if now - last_alert < self.cooldown:
            print(f"⚠️  Alert type '{alert_type}' is in cooldown")
            return True
            
        # Check rate limit for this alert type
        if len(self.alert_history[alert_type]) >= self.rate_limit:
            print(f"⚠️  Rate limit reached for alert type '{alert_type}'")
            return True
            
        return False

    def generate_alert_message(self, anomaly_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable alert message
        
        Args:
            anomaly_data: Dictionary containing anomaly details
            
        Returns:
            str: Generated alert message
        """
        # If we have an API client, use it to generate a detailed message
        if self.client:
            try:
                prompt = f"""
                You are a network security analyst. Generate a clear and concise alert message for the following anomaly detection:
                
                Anomaly Details:
                {json.dumps(anomaly_data, indent=2)}
                
                Please provide:
                1. A brief summary of the anomaly
                2. Potential impact
                3. Recommended actions
                4. Severity level (Low/Medium/High/Critical)
                
                Format the response as a clear, well-structured message.
                """
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that generates clear and concise security alerts."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                print(f"Error generating alert message: {str(e)}")
        
        # Fallback to a simple message if API call fails or no API key
        timestamp = anomaly_data.get('timestamp', datetime.now().isoformat())
        score = anomaly_data.get('score', 'unknown')
        severity = anomaly_data.get('severity', 'unknown').upper()
        
        return (
            f"SECURITY ALERT - {severity} SEVERITY\n"
            f"Time: {timestamp}\n"
            f"Anomaly Score: {score:.4f}\n"
            f"Details: {json.dumps(anomaly_data.get('features', {}), indent=2)[:500]}"
        )

    def send_alert(self, anomaly_data: Dict[str, Any], recipients: List[str] = None) -> Dict[str, Any]:
        """
        Generate and send an alert with rate limiting
        
        Args:
            anomaly_data: Dictionary containing anomaly details
            recipients: Optional list of recipient emails/IDs
            
        Returns:
            dict: Alert details including status and message
        """
        try:
            # Get alert type from severity or default to 'unknown'
            alert_type = anomaly_data.get('severity', 'unknown')
            
            # Check rate limiting
            if self._is_rate_limited(alert_type):
                return {
                    "status": "rate_limited",
                    "message": f"Alert rate limit reached for type: {alert_type}",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Generate the alert message
            alert_message = self.generate_alert_message(anomaly_data)
            
            # Update alert history and cooldowns
            now = time.time()
            self.alert_history[alert_type].append(now)
            self.alert_cooldowns[alert_type] = now
            
            # Clean up old history to prevent memory issues
            for alert_type in list(self.alert_history.keys()):
                self.alert_history[alert_type] = [
                    t for t in self.alert_history[alert_type]
                    if now - t < 3600  # Keep only last hour of history
                ]
                
                # Remove empty alert types
                if not self.alert_history[alert_type]:
                    del self.alert_history[alert_type]
            
            # Print the alert (in production, you might send an email, Slack message, etc.)
            print("\n" + "="*50)
            print(f"🚨 {alert_type.upper()} SEVERITY ALERT")
            print("="*50)
            print(alert_message)
            print("="*50 + "\n")
            
            # Here you would implement actual notification logic
            # For example, sending email, Slack message, etc.
            # self._send_email(recipients, alert_message)
            # self._send_slack_notification(alert_message)
            
            return {
                "status": "success",
                "message": f"Alert generated and sent (Type: {alert_type})",
                "alert_type": alert_type,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error sending alert: {str(e)}"
            print(f" {error_msg}")
            return {
                "status": "error",
                "message": error_msg,
                "timestamp": datetime.now().isoformat()
            }
