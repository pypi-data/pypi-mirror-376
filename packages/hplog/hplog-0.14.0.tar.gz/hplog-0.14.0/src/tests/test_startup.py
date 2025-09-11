# tests/test_startup.py
from pydantic import BaseModel
import pytest
from hplog.hplog import HPLog, Connector


class SomeModel(BaseModel):
    id: int
    name: str


@pytest.fixture
def connection_uri_mongo():
    return "mongodb://root:example@127.0.0.1:27017/example?authSource=admin"


@pytest.fixture
def pydantic_model():
    m = SomeModel(id=1, name="Test")
    yield m


@pytest.fixture
def mongo_connector(connection_uri_mongo):
    c = Connector(connection_uri_mongo, sql_mode=False)
    yield c


@pytest.fixture
def hplog_instance_mongo(mongo_connector):
    hp = HPLog(mongo_connector)
    yield hp


@pytest.fixture
def hplog_instance(mysql_connector):
    hp = HPLog(mysql_connector)
    return hp


@pytest.fixture
def mysql_uri():
    return "mysql+pymysql://root:password@localhost:3306/testdb"


@pytest.fixture
def mysql_connector(mysql_uri):
    c = Connector(mysql_uri, sql_mode=True)
    yield c


def test_connector_str(mongo_connector, connection_uri_mongo):
    assert str(mongo_connector) == connection_uri_mongo, (
        "Connector __str__ method did not return the expected URI."
    )


@pytest.mark.asyncio
async def test_hplog_model(hplog_instance_mongo, pydantic_model):
    hp = hplog_instance_mongo
    result = await hp.log(pydantic_model)
    assert result is not None, "Logging failed, no result returned."


@pytest.mark.asyncio
async def test_get_logs(hplog_instance_mongo: HPLog, pydantic_model):
    hp = hplog_instance_mongo
    await hp.log(pydantic_model)
    print(await hp.get_logs())


@pytest.mark.asyncio
async def test_hplog_get_log_df(hplog_instance_mongo: HPLog, pydantic_model):
    hp = hplog_instance_mongo
    await hp.log(pydantic_model)
    df = await hp.get_logs.to_pandas()
    assert not df.empty, "DataFrame is empty."
    assert list(df.columns) == ["_id", "id", "name"], "DataFrame columns do not match expected."
    assert df.iloc[0]["id"] == pydantic_model.id, "Logged id does not match."
    assert df.iloc[0]["name"] == pydantic_model.name, "Logged name does not match."
