from datetime import datetime
from typing import Dict, Tuple
import requests
from requests.auth import HTTPBasicAuth

from cc_clients_python_lib.http_status import HttpStatus


__copyright__  = "Copyright (c) 2025 Jeffrey Jonathan Jennings"
__license__    = "MIT"
__credits__    = ["Jeffrey Jonathan Jennings (J3)"]
__maintainer__ = "Jeffrey Jonathan Jennings (J3)"
__email__      = "j3@thej3.com"
__status__     = "dev"

# Metrics Config Keys.
METRICS_CONFIG = {
    "confluent_cloud_api_key": "confluent_cloud_api_key",
    "confluent_cloud_api_secret": "confluent_cloud_api_secret"
}

class MetricsClient():
    def __init__(self, metrics_config: Dict):
        self.confluent_cloud_api_key = metrics_config[METRICS_CONFIG["confluent_cloud_api_key"]]
        self.confluent_cloud_api_secret = metrics_config[METRICS_CONFIG["confluent_cloud_api_secret"]]
        self.metrics_base_url = "https://api.telemetry.confluent.cloud/v2/metrics/cloud"

    def get_topic_total_bytes(self, kafka_cluster_id: str, topic_name: str, query_start_time: datetime, query_end_time: datetime) -> Tuple[int, str, Dict | None]:
        """This function retrieves the total bytes for a given Kafka topic within a specified time range.

        Args:
            kafka_cluster_id (str): The Kafka cluster ID.
            topic_name (str): The Kafka topic name.
            query_start_time (datetime): The start time for the query.
            query_end_time (datetime): The end time for the query.
            
        Returns:
            Tuple[int, str, Dict | None]: A tuple containing the HTTP status code, error
            message (if any), and a dictionary with total bytes, total records, average bytes per record,
            period start and end times, and source if successful; otherwise, None.
        """
        try:
            # Convert datetime to ISO format with milliseconds
            query_start_iso = query_start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            query_end_iso = query_end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            # Query for received bytes and records
            query_data = {
                "aggregations": [
                    {
                        "agg": "SUM",
                        "metric": "io.confluent.kafka.server/received_bytes"
                    }
                ],
                "filter": {
                    "op": "AND",
                    "filters": [
                        {
                            "field": "metric.topic", 
                            "op": "EQ", 
                            "value": topic_name
                        },
                        {
                            "field": "resource.kafka.id", 
                            "op": "EQ", 
                            "value": kafka_cluster_id
                        },
                    ],
                },
                "granularity": "PT1H",
                "group_by": [
                    "metric.topic"
                ],
                "intervals": [
                    f"{query_start_iso}/{query_end_iso}"
                ]
            }
            print("Query Data:", query_data)
            
            response = requests.post(url=f"{self.metrics_base_url}/query",
                                     auth=HTTPBasicAuth(self.confluent_cloud_api_key, self.confluent_cloud_api_secret),
                                     json=query_data,
                                     timeout=30)
            
            try:
                # Raise HTTPError, if occurred.
                response.raise_for_status()

                data = response.json()

                # Aggregate results by metric
                totals = 0
                for result in data.get("data", []):
                    totals += result.get("value", 0)

                return HttpStatus.OK, "", {
                    'total_bytes': totals,
                    'period_start': query_start_time.isoformat(),
                    'period_end': query_end_time.isoformat(),
                    'source': 'metrics_api'
                }
            except requests.exceptions.RequestException as e:
                return response.status_code, f"Metrics API Request failed for topic {topic_name} because {e}.  The error details are: {response.json() if response.content else {}}", None
        except Exception as e:
            return HttpStatus.BAD_REQUEST, f"Fail to query the Metrics API for topic {topic_name} because {e}.  The error details are: {response.json() if response.content else {}}", None

    def get_topic_total_records(self, kafka_cluster_id: str, topic_name: str, query_start_time: datetime, query_end_time: datetime) -> Tuple[int, str, Dict | None]:
        """This function retrieves the total records for a given Kafka topic within a specified time range.

        Args:
            kafka_cluster_id (str): The Kafka cluster ID.
            topic_name (str): The Kafka topic name.
            query_start_time (datetime): The start time for the query.
            query_end_time (datetime): The end time for the query.
            
        Returns:
            Tuple[int, str, Dict | None]: A tuple containing the HTTP status code, error
            message (if any), and a dictionary with total bytes, total records, average bytes per record,
            period start and end times, and source if successful; otherwise, None.
        """
        try:
            # Convert datetime to ISO format with milliseconds
            query_start_iso = query_start_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            query_end_iso = query_end_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

            # Query for received bytes and records
            query_data = {
                "aggregations": [
                    {
                        "agg": "SUM",
                        "metric": "io.confluent.kafka.server/received_records"
                    }
                ],
                "filter": {
                    "op": "AND",
                    "filters": [
                        {
                            "field": "metric.topic", 
                            "op": "EQ", 
                            "value": topic_name
                        },
                        {
                            "field": "resource.kafka.id", 
                            "op": "EQ", 
                            "value": kafka_cluster_id
                        },
                    ],
                },
                "granularity": "PT1H",
                "group_by": [
                    "metric.topic"
                ],
                "intervals": [
                    f"{query_start_iso}/{query_end_iso}"
                ]
            }
            print("Query Data:", query_data)
            
            response = requests.post(url=f"{self.metrics_base_url}/query",
                                     auth=HTTPBasicAuth(self.confluent_cloud_api_key, self.confluent_cloud_api_secret),
                                     json=query_data,
                                     timeout=30)
            
            try:
                # Raise HTTPError, if occurred.
                response.raise_for_status()

                data = response.json()

                # Aggregate results by metric
                totals = 0
                for result in data.get("data", []):
                    totals += result.get("value", 0)
                
                return HttpStatus.OK, "", {
                    'total_records': totals,
                    'period_start': query_start_time.isoformat(),
                    'period_end': query_end_time.isoformat(),
                    'source': 'metrics_api'
                }
            except requests.exceptions.RequestException as e:
                return response.status_code, f"Metrics API Request failed for topic {topic_name} because {e}.  The error details are: {response.json() if response.content else {}}", None
        except Exception as e:
            return HttpStatus.BAD_REQUEST, f"Fail to query the Metrics API for topic {topic_name} because {e}.  The error details are: {response.json() if response.content else {}}", None
