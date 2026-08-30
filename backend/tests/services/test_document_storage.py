from io import BytesIO

import pytest

from backend.app.adapters.document_storage import DocumentStorage
from backend.app.core.errors import AppError


def test_storage_streams_file_and_calculates_stable_sha256(tmp_path):
    storage = DocumentStorage(tmp_path, max_size_bytes=1024)

    stored = storage.save(BytesIO(b"hello"), "doc-1", "../manual.txt", user_id="user-1")
    stored_again = storage.save(BytesIO(b"hello"), "doc-2", "manual.txt", user_id="user-1")

    assert stored.size_bytes == 5
    assert stored.sha256 == stored_again.sha256
    assert stored.storage_path.startswith(str(tmp_path / "user-1"))
    assert ".." not in stored.storage_path


def test_storage_rejects_empty_and_oversized_files(tmp_path):
    storage = DocumentStorage(tmp_path, max_size_bytes=4)

    with pytest.raises(AppError) as empty_error:
        storage.save(BytesIO(b""), "doc-empty", "empty.txt")
    assert empty_error.value.code == "EMPTY_FILE"

    with pytest.raises(AppError) as large_error:
        storage.save(BytesIO(b"12345"), "doc-large", "large.txt")
    assert large_error.value.code == "FILE_TOO_LARGE"

