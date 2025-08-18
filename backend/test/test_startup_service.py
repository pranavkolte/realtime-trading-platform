import pytest
from unittest.mock import patch, MagicMock

from app.api.services import startup_service

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    yield session

@pytest.fixture
def mock_matching_engine():
    with patch("app.api.services.startup_service.matching_engine") as mock_engine:
        yield mock_engine

@pytest.fixture
def mock_get_db_session(mock_db_session):
    with patch("app.api.services.startup_service.get_db_session", return_value=iter([mock_db_session])):
        yield

def test_restore_matching_engine_success(mock_get_db_session, mock_db_session, mock_matching_engine):
    # Mock last trade
    last_trade = MagicMock(price=100)
    mock_db_session.query().order_by().first.return_value = last_trade
    # Mock active orders
    active_orders = [MagicMock(), MagicMock()]
    mock_db_session.query().filter().order_by().all.return_value = active_orders

    startup_service.restore_matching_engine_from_database()

    mock_matching_engine.set_last_trade_price.assert_called_once_with(100)
    mock_matching_engine.restore_from_database.assert_called_once_with(active_orders, mock_db_session)
    mock_db_session.close.assert_called_once()

def test_restore_matching_engine_no_last_trade(mock_get_db_session, mock_db_session, mock_matching_engine):
    # No last trade
    mock_db_session.query().order_by().first.return_value = None
    # Mock active orders
    active_orders = []
    mock_db_session.query().filter().order_by().all.return_value = active_orders

    startup_service.restore_matching_engine_from_database()

    mock_matching_engine.set_last_trade_price.assert_not_called()
    mock_matching_engine.restore_from_database.assert_called_once_with(active_orders, mock_db_session)
    mock_db_session.close.assert_called_once()

def test_restore_matching_engine_db_exception(mock_get_db_session, mock_db_session, mock_matching_engine):
    # Simulate exception during query
    mock_db_session.query.side_effect = Exception("DB error")
    with pytest.raises(Exception):
        startup_service.restore_matching_engine_from_database()
    mock_db_session.close.assert_called_once()