from pathlib import Path
def test_safe_candidate():
 root=Path(__file__).parent.parent
 assert (root/'safe-result.txt').read_text()=='before'
 assert (root/'.developer_staging/safe-action/safe-result.txt').read_text()=='after'
