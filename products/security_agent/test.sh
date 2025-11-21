python security_agent.py \
  --url "http://localhost:5000" \
  --token "Bearer token_user_a" \
  --spec "openapi.yaml" \
  --victim-id "102"

#### 2. To Test YOUR Existing API
Replace the values with your actual API details:

```bash
python security_agent.py \
  --url "https://api.your-company.com/v1" \
  --token "Bearer eyJhbGciOiJIUzI1Ni..." \
  --spec "./docs/my_swagger.json" \
  --victim-id "550e8400-e29b-41d4-a716-446655440000"

**Arguments Explained:**
* `--url`: The root URL where your API is hosted.
* `--token`: A valid JWT or API Key for a standard user (the "Attacker").
* `--spec`: Path to your local OpenAPI/Swagger file, OR a URL to the raw JSON/YAML.
* `--victim-id`: A valid ID of *another* user in your system. The agent will try to steal this user's data using the token you provided.