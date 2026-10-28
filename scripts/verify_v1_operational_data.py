"""Read-only operational-document preparation; no model calls or active DB writes."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.knowledge.official_knowledge_ingestion import validate_operational_manifest
parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('--output',type=Path)
args=parser.parse_args();report=validate_operational_manifest(args.manifest)
text=json.dumps(report,indent=2,ensure_ascii=False)
if args.output:
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text,encoding='utf-8')
print(text)
raise SystemExit(2 if report['blockers'] else 0)
