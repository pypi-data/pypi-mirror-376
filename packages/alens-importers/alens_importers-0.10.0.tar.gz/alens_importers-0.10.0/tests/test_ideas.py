"""
The names here are ideas for additional tests and features.
None of them pass as they are not implemented yet.
"""
import pytest

@pytest.mark.skip(reason="Test idea")
def test_stock_sale():
    """Stock sale"""
    assert False


@pytest.mark.skip(reason="Test idea")
def test_other_fees():
    """Other fees"""
    assert False


@pytest.mark.skip(reason="Test idea")
def test_issue_change():
    """Handle issue change"""
    # importer = ibflex.Importer(ibflex_config)
    # run_importer_test_with_existing_entries(importer, "issue-change.xml")
    assert False


@pytest.mark.skip(reason="Test idea")
def test_corporate_actions():
    """Handle corporate actions"""
    # importer = ibflex.Importer(ibflex_config)
    # run_importer_test_with_existing_entries(importer, "corp-actions.xml")
    assert False


@pytest.mark.skip(reason="Test idea")
def test_stock_merger():
    """Handle stock merger"""
    # importer = ibflex.Importer(ibflex_config)
    # run_importer_test_with_existing_entries(importer, "stock-merger.xml")
    assert False


@pytest.mark.skip(reason="Test idea")
def test_stock_split():
    """Handle stock split"""
    # importer = ibflex.Importer(ibflex_config)
    # run_importer_test_with_existing_entries(importer, "stock-split.xml")
    assert False


@pytest.mark.skip(reason="Test idea")
def test_report_unknown_records():
    """Report unknown records to the console?"""
    assert False
