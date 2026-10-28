import hashlib
import io
import tarfile

import pytest

from app.improvement.release import create_backup, restore_backup


def test_backup_restore_verifies_content_and_refuses_overwrite(tmp_path):
    source = tmp_path / "data"
    source.mkdir()
    (source / "state.json").write_text('{"version":"baseline"}')
    backup = create_backup(source, tmp_path / "backups", "staging")
    restored = restore_backup(backup, tmp_path / "restored")
    assert (restored / "data/state.json").read_bytes() == (source / "state.json").read_bytes()
    with pytest.raises(ValueError, match="empty"):
        restore_backup(backup, restored)
    backup.write_bytes(backup.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="checksum"):
        restore_backup(backup, tmp_path / "bad")


@pytest.mark.parametrize("name,kind", [("../escape", "file"), ("/absolute", "file"),
                                     ("dir/link", "symlink"), ("C:/private", "file")])
def test_malicious_archive_cannot_write_outside_restore(tmp_path, name, kind):
    path = tmp_path / "unsafe.tar.gz"
    with tarfile.open(path, "w:gz") as archive:
        item = tarfile.TarInfo(name)
        if kind == "symlink":
            item.type = tarfile.SYMTYPE
            item.linkname = "../../private"
            archive.addfile(item)
        else:
            item.size = 3
            archive.addfile(item, io.BytesIO(b"bad"))
    path.with_suffix(".gz.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="unsafe"):
        restore_backup(path, tmp_path / "restored")
    assert not (tmp_path / "escape").exists()
