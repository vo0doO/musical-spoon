from fastapi import status
from sqlalchemy import select

from orders.domain.model import Order, OrderStatuses


class TestPostOrder:
    def test_returns_200_and_create_basket_if_user_does_not_have_a_basket(self, api_client, fake_order):
        response = api_client.post('/order/')
        assert response.status_code == status.HTTP_200_OK

        order = response.json()
        assert order['user_id'] == fake_order.user_id
        assert order['tickets'] == []

    def test_returns_200_and_retrieve_basket_if_user_has_a_basket(self, api_client, sqlite_fake_orders):
        expected_order = sqlite_fake_orders[0]
        expected_tickets = [ticket.model_dump() for ticket in expected_order.tickets]

        response = api_client.post('/order/', headers={'X-User-Id': expected_order.user_id})
        assert response.status_code == status.HTTP_200_OK

        order = response.json()
        assert order['id'] == expected_order.id
        assert order['user_id'] == expected_order.user_id
        assert order['tickets'] == expected_tickets


class TestPutOrder:
    def test_returns_200_and_update_basket_with_valid_tickets(self, api_client, sqlite_fake_orders):
        expected_order = sqlite_fake_orders[0]
        expected_tickets = [{'event_id': 101, 'price': 100.00}, {'event_id': 102, 'price': 200.00}]

        response = api_client.put('/order/', headers={'X-User-Id': expected_order.user_id}, json=expected_tickets)
        assert response.status_code == status.HTTP_200_OK

        updated_order = response.json()
        updated_tickets = [{'event_id': t['event_id'], 'price': t['price']} for t in updated_order['tickets']]

        assert updated_tickets == expected_tickets

    def test_returns_404_and_not_update_basket_if_user_does_not_have_a_basket(self, api_client, fake_order):
        response = api_client.put('/order/', json=[])
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == f'Basket not found for user: {fake_order.user_id}'


class TestDeleteOrder:
    async def test_returns_200_and_delete_order_if_the_order_is_done_and_of_this_user(
        self,
        api_client,
        sqlite_session,
        sqlite_fake_orders,
    ):
        expected_order = next((order for order in sqlite_fake_orders if order.order_status == OrderStatuses.DONE), None)
        response = api_client.delete(f'/order/{expected_order.id}', headers={'X-User-Id': expected_order.user_id})
        assert response.status_code == status.HTTP_200_OK

        result = await sqlite_session.execute(select(Order))
        orders = result.unique().scalars().all()
        assert expected_order not in orders

    async def test_returns_404_and_not_delete_order_if_order_does_not_exist(self, api_client, sqlite_fake_orders):
        non_existent_order_id = 9999
        response = api_client.delete(
            f'/order/{non_existent_order_id}',
            headers={'X-User-Id': sqlite_fake_orders[0].user_id},
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()['detail'] == f'Order with id {non_existent_order_id} not found'

    async def test_returns_403_and_not_delete_order_if_order_does_not_belong_user(self, api_client, sqlite_fake_orders):
        order = sqlite_fake_orders[0]
        wrong_user_id = order.user_id[:-2] + '99'
        response = api_client.delete(f'/order/{order.id}', headers={'X-User-Id': wrong_user_id})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()['detail'] == f'Order {order.id} does not belong to this user: {wrong_user_id}'
