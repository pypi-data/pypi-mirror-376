# Meridian SDK for Python

Official Python SDK for the Meridian AI Search API - Enterprise search across connected data sources.

## Features

- **AI-Powered Search**: Natural language search across SharePoint, Google Drive, and more
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Usage Tracking**: Monitor API usage and billing in real-time
- **Secure Authentication**: Bearer token authentication with API key management
- **Async Support**: Full async/await support for high-performance applications
- **Type Hints**: Complete type annotations for better IDE support

## Installation

```bash
pip install meridian-sdk
```

## Quick Start

```python
from meridian_sdk import MeridianAPI
import asyncio

async def main():
    # Initialize the client
    async with MeridianAPI(api_key="your_api_key_here") as client:
        
        # Perform a search
        response = await client.search(
            prompt="What are our Q4 sales numbers?",
            processing_mode="agentic",
            include_sources=True
        )
        
        if response.success:
            print(f"Answer: {response.data['answer']}")
            print(f"Sources: {response.data.get('sources', [])}")
        else:
            print(f"Error: {response.error}")

# Run the async function
asyncio.run(main())
```

## Authentication

Get your API key from the [Meridian Dashboard](https://dashboard.trymeridian.dev) and set it as an environment variable:

```bash
export MERIDIAN_API_KEY="your_api_key_here"
```

Then use it in your code:

```python
import os
from meridian_sdk import MeridianAPI

api_key = os.getenv("MERIDIAN_API_KEY")
client = MeridianAPI(api_key=api_key)
```

## Core Features

### Search

Perform AI-powered searches across your connected data sources:

```python
response = await client.search(
    prompt="Find all documents about project Apollo",
    conversation_id="optional_conversation_id",  # For context continuity
    processing_mode="agentic",  # 'auto', 'standard', or 'agentic'
    max_results=10,
    sources=["sharepoint", "google_drive"],  # Filter by source
    include_sources=True,
    include_related=True
)
```

### Usage & Billing

Monitor your API usage and billing:

```python
# Get detailed usage statistics
usage = await client.get_usage()
print(f"Searches this month: {usage.data['searches_count']}")
print(f"Current balance: ${usage.data['balance']}")

# Check rate limits
limits = await client.get_limits()
print(f"Rate limit: {limits.data['rate_limit']}/min")
print(f"Remaining: {limits.data['remaining']}")
```

### Connector Management

Manage your data source connections:

```python
# Check connector status
status = await client.get_connector_status()
for connector in status.data['connectors']:
    print(f"{connector['name']}: {connector['status']}")

# Connect a new data source
response = await client.connect_data_source(provider="microsoft")
print(f"Auth URL: {response.data['auth_url']}")
```

### Health & Status

Monitor API health and status:

```python
# Health check
health = await client.health_check()
print(f"API Status: {health.data['status']}")
print(f"Response time: {health.data['response_time_ms']}ms")

# Get API capabilities
status = await client.get_status()
print(f"Version: {status.data['version']}")
print(f"Features: {status.data['features']}")
```

## Advanced Usage

### Custom Configuration

```python
client = MeridianAPI(
    api_key="your_api_key",
    base_url="https://dashboard.trymeridian.dev",  # Custom endpoint
    timeout=60,  # Request timeout in seconds
    max_retries=5  # Maximum retry attempts
)
```

### Error Handling

```python
from meridian_sdk import MeridianAPIError

try:
    response = await client.search("test query")
except MeridianAPIError as e:
    print(f"API Error: {e.message}")
    print(f"Status Code: {e.status_code}")
    print(f"Response: {e.response}")
```

### Rate Limit Information

```python
response = await client.search("test query")
rate_info = client.get_rate_limit_info(response)
print(f"Limit: {rate_info['limit']}")
print(f"Remaining: {rate_info['remaining']}")
print(f"Reset at: {rate_info['reset_time']}")
```

### Validation

Validate requests before executing them:

```python
validation = await client.validate_request(
    prompt="What are our sales numbers?",
    processing_mode="agentic"
)

if validation.data['valid']:
    # Proceed with actual search
    response = await client.search(prompt="What are our sales numbers?")
else:
    print(f"Invalid request: {validation.data['errors']}")
```

## Response Structure

All API methods return an `APIResponse` object:

```python
@dataclass
class APIResponse:
    success: bool           # Whether the request succeeded
    data: Any              # Response data (dict, list, or string)
    status_code: int       # HTTP status code
    headers: Dict[str, str]  # Response headers
    error: Optional[str]    # Error message if failed
```

## Examples

### Contextual Conversations

Maintain context across multiple searches:

```python
conversation_id = "conv_123456"

# First query
response1 = await client.search(
    prompt="What were our Q4 sales?",
    conversation_id=conversation_id
)

# Follow-up query with context
response2 = await client.search(
    prompt="How does that compare to Q3?",
    conversation_id=conversation_id
)
```

### Batch Processing

Process multiple searches efficiently:

```python
queries = [
    "Q4 sales report",
    "Employee handbook vacation policy",
    "Latest product roadmap"
]

tasks = [client.search(prompt=q) for q in queries]
responses = await asyncio.gather(*tasks)

for query, response in zip(queries, responses):
    print(f"{query}: {response.data.get('answer', 'No answer')}")
```

### Export Results

Export search results to different formats:

```python
import json
import csv

response = await client.search("All customer feedback from last month")

# Export as JSON
with open('results.json', 'w') as f:
    json.dump(response.data, f, indent=2)

# Export as CSV (for structured results)
if 'results' in response.data:
    with open('results.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'summary', 'source'])
        writer.writeheader()
        for result in response.data['results']:
            writer.writerow(result)
```

## Best Practices

1. **Use Environment Variables**: Store API keys securely in environment variables
2. **Implement Retry Logic**: The SDK has built-in retries, but implement application-level retries for critical operations
3. **Monitor Rate Limits**: Check rate limit headers and implement backoff when needed
4. **Use Conversation IDs**: Maintain context for related queries
5. **Validate Before Executing**: Use the validation endpoint for user-generated queries
6. **Close Connections**: Use async context managers (`async with`) to ensure proper cleanup

## Support

- Email: support@trymeridian.dev
- Documentation: https://www.trymeridian.dev/docs

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes.

---

Built by the Meridian Team