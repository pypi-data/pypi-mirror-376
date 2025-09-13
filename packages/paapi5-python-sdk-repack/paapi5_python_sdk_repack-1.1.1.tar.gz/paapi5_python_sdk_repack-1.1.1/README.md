# paapi5-python-sdk (repack)

**Import name remains `paapi5_python_sdk`** while the distribution name on PyPI may differ (e.g., `paapi5-python-sdk-repack`).

## Install
```bash
pip install paapi5-python-sdk-repack
```

## Quick Start
```python
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.api_client import ApiClient
from paapi5_python_sdk.configuration import Configuration

conf = Configuration(
  access_key="YOUR_KEY",
  secret_key="YOUR_SECRET",
  host="webservices.amazon.co.jp",
  region="us-west-2",
)
api = DefaultApi(ApiClient(conf))
# api.search_items(...), api.get_browse_nodes(...), etc.
```

## License / Attribution
- Licensed under Apache License 2.0. See COPYING.txt.
- The original NOTICE.txt is included unchanged.
- This package repackages the original PA-API 5.0 sample SDK for distribution on PyPI.
- It is unofficial and not affiliated with or endorsed by Amazon.
