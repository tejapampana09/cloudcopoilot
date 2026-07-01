import os
import pytest
import tempfile
from app.services.scanner import HeuristicScanner

def test_scan_repository_non_existent():
    # Scanning a non-existent path should raise ValueError
    with pytest.raises(ValueError):
        HeuristicScanner.scan_repository("non-existent-path-for-testing")

def test_scan_repository_empty_dir():
    # Scanning an empty directory should return default empty metadata
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata = HeuristicScanner.scan_repository(tmpdir)
        assert metadata.languages == []
        assert metadata.frameworks == []
        assert metadata.databases == []
        assert metadata.docker_readiness is False
