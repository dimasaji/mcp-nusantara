"""Read the existing local provider inventory; never generate/install a model."""
import asyncio
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from app.core.config import settings
from app.models.ollama import OllamaProvider

async def main():
    configuration = settings.effective_configuration
    result = {'timestamp': datetime.now(timezone(timedelta(hours=7))).isoformat(),
              'provider': configuration.llm.provider, 'generation_performed': False,
              'production_configuration_changed': False}
    if urlsplit(configuration.llm.base_url).hostname not in {'127.0.0.1', '::1', 'localhost'}:
        result.update(status='NOT_VERIFIED', reason='LOCAL_PROVIDER_REQUIRED')
    else:
        provider = OllamaProvider(nusantara_config=configuration)
        try:
            models = await asyncio.wait_for(provider.list_models(), timeout=10)
            result.update(status='PASS_SCOPED', availability='INVENTORY_OBSERVED',
                          models=[m['name'] for m in models if isinstance(m, dict) and isinstance(m.get('name'), str)])
        except Exception as exc:
            result.update(status='NOT_VERIFIED', reason='LOCAL_INVENTORY_UNAVAILABLE', error_type=type(exc).__name__)
        finally:
            await provider.close()
    with (OUT / 'LOCAL_PROVIDER_INVENTORY.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))

asyncio.run(main())
