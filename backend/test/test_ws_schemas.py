import pytest
from datetime import datetime
from app.schemas.ws_schemas import (
    WSTradeExecutionSchema,
    WSOrderBookUpdateSchema,
    WSOrderStatusSchema,
    WSErrorSchema,
    WSConnectionSchema,
)


@pytest.fixture
def now():
    return datetime.utcnow()


def test_wstradeexecutionschema_valid(now):
    data = {
        "event": "trade_executed",
        "timestamp": now,
        "data": {"price": 100, "qty": 1},
    }
    obj = WSTradeExecutionSchema(**data)
    assert obj.event == "trade_executed"
    assert obj.data["price"] == 100


def test_wsorderbookupdateschema_valid(now):
    data = {"timestamp": now, "data": {"bids": [], "asks": []}}
    obj = WSOrderBookUpdateSchema(**data)
    assert obj.event == "book_update"
    assert "bids" in obj.data


def test_wsorderstatusschema_valid(now):
    data = {"timestamp": now, "data": {"status": "filled"}}
    obj = WSOrderStatusSchema(**data)
    assert obj.event == "order_status"
    assert obj.data["status"] == "filled"


def test_wserrorschema_valid():
    obj = WSErrorSchema(message="Something went wrong")
    assert obj.event == "error"
    assert obj.message == "Something went wrong"


def test_wsconnectionschema_valid():
    obj = WSConnectionSchema(message="Connected", user_id="u1")
    assert obj.event == "connected"
    assert obj.user_id == "u1"


@pytest.mark.parametrize(
    "model,missing",
    [
        (WSTradeExecutionSchema, "timestamp"),
        (WSOrderBookUpdateSchema, "timestamp"),
        (WSOrderStatusSchema, "timestamp"),
    ],
)
def test_required_fields_missing(model, missing):
    with pytest.raises(Exception):
        model(data={})


def test_wserrorschema_missing_message():
    with pytest.raises(Exception):
        WSErrorSchema()


def test_wsconnectionschema_missing_fields():
    with pytest.raises(Exception):
        WSConnectionSchema()
