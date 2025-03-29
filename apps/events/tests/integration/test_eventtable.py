import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.integration


def get_insert_event_query(returning_id=False):
    query = """
        INSERT INTO event (name, description, event_date, available_tickets, ticket_price)
        VALUES (:name, :description, :event_date, :available_tickets, :ticket_price);
    """

    if returning_id:
        query = query.replace(';', '\nRETURNING id')

    return text(query)


async def test_event_have_btree_idx_on_event_date(postgres_session: AsyncSession):
    query = text("""
        SELECT a.amname AS index_type
        FROM pg_index i
        JOIN pg_class c ON i.indexrelid = c.oid
        JOIN pg_am a ON c.relam = a.oid
        JOIN pg_class t ON i.indrelid = t.oid
        WHERE t.relname = 'event' AND c.relname = 'idx_event_date';
    """)

    result = await postgres_session.execute(query)
    index_type = result.scalar()

    assert index_type == 'btree'


async def test_autoincrement_id(postgres_session: AsyncSession, fake_event: dict):
    query = get_insert_event_query(returning_id=True)

    result_1 = await postgres_session.execute(query, fake_event)
    id_1 = result_1.scalar()
    result_2 = await postgres_session.execute(query, fake_event)
    id_2 = result_2.scalar()

    assert id_2 is not None
    assert id_1 is not None
    assert id_2 == id_1 + 1

    select_query = text('SELECT * FROM event ORDER BY id ASC')
    result = await postgres_session.execute(select_query)
    events = result.fetchall()
    ids = [row._asdict()['id'] for row in events]

    assert ids == [id_1, id_2], 'The order of the ID in the database is incorrect'


async def test_can_insert_event(postgres_session: AsyncSession, fake_event: dict):
    query = get_insert_event_query(returning_id=True)

    result = await postgres_session.execute(query, fake_event)
    event_id = result.scalar()

    assert event_id is not None

    select_query = text('SELECT * FROM event WHERE id = :id')
    result = await postgres_session.execute(select_query, {'id': event_id})
    event = result.fetchone()._asdict()

    assert event is not None
    assert event['name'] == fake_event['name']
    assert event['ticket_price'] == fake_event['ticket_price']


async def test_cant_insert_event_with_negative_available_tickets(postgres_session: AsyncSession, fake_event: dict):
    query = get_insert_event_query()

    fake_event['available_tickets'] = -5

    with pytest.raises(Exception, match='check_available_tickets_non_negative'):
        await postgres_session.execute(query, fake_event)


async def test_cant_insert_event_with_negative_ticket_price(postgres_session: AsyncSession, fake_event: dict):
    query = get_insert_event_query()

    fake_event['ticket_price'] = -5

    with pytest.raises(Exception, match='check_ticket_price_positive'):
        await postgres_session.execute(query, fake_event)
