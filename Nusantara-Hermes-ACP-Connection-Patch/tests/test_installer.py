import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',BASE/'install_patch.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)

def digest(data): return hashlib.sha256(data).hexdigest()

class InstallTests(unittest.TestCase):
    def fixture(self, base):
        root=base/'repo';pkg=base/'package'
        (root/'app').mkdir(parents=True);(pkg/'payload/app').mkdir(parents=True)
        (root/'app/main.py').write_bytes(b'# before\n')
        (pkg/'payload/app/main.py').write_bytes(b'# after\n')
        (pkg/'payload/app/bridge.py').write_bytes(b'# new\n')
        rows=[{'path':'app/main.py','before_sha256':digest(b'# before\n'),'after_sha256':digest(b'# after\n')},
              {'path':'app/bridge.py','before_sha256':None,'after_sha256':digest(b'# new\n')}]
        (pkg/'manifest.json').write_text(json.dumps({'files':rows}))
        return root,pkg

    def test_dry_run_no_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));installer.install(root,pkg)
            self.assertFalse((root/'app/bridge.py').exists())
            self.assertFalse((root/'.developer_backups').exists())

    def test_reject_dirty_source_no_partial_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));(root/'app/main.py').write_bytes(b'# user changes\n')
            with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):
                installer.install(root,pkg,True)
            self.assertFalse((root/'app/bridge.py').exists())
            self.assertEqual((root/'app/main.py').read_bytes(),b'# user changes\n')

    def test_existing_new_file_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));(root/'app/bridge.py').write_bytes(b'# existing\n')
            with self.assertRaisesRegex(ValueError,'SOURCE_CHANGED'):
                installer.install(root,pkg,True)
            self.assertEqual((root/'app/main.py').read_bytes(),b'# before\n')

    def test_backup_and_success(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));backup=installer.install(root,pkg,True)
            self.assertEqual((backup/'app/main.py').read_bytes(),b'# before\n')
            self.assertEqual((root/'app/main.py').read_bytes(),b'# after\n')
            self.assertTrue((root/'app/bridge.py').is_file())
            self.assertFalse((root/'.nusantara-hermes-patch.lock').exists())

    def test_rollback_on_second_write_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));replace=installer.os.replace
            calls=[]
            def fail_second(a,b):
                calls.append(1)
                if len(calls)==2: raise OSError('simulated disk error')
                return replace(a,b)
            with patch.object(installer.os,'replace',side_effect=fail_second):
                with self.assertRaises(OSError): installer.install(root,pkg,True)
            self.assertEqual((root/'app/main.py').read_bytes(),b'# before\n')
            self.assertFalse((root/'app/bridge.py').exists())

    def test_corrupt_payload_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root,pkg=self.fixture(Path(folder));(pkg/'payload/app/bridge.py').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'PAYLOAD_HASH'):
                installer.install(root,pkg,True)

if __name__=='__main__': unittest.main()
