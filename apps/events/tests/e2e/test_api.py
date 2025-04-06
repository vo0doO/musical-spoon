from datetime import datetime, timedelta

import pytest
from fastapi import status

pytestmark = pytest.mark.e2e


class TestForUserRouter:
    class TestGetEvent:
        def test_returns_200_and_event_if_getting_exists_event(self, api_client, pg_fake_events):
            response = api_client.get('/events/1')

            assert response.status_code == status.HTTP_200_OK

            returned_event = response.json()
            expected_event = pg_fake_events[0].model_dump(mode='json')

            assert returned_event == expected_event

        def test_returns_403_and_error_message_if_getting_event_with_unavailable_x_user_role_header(self, api_client):
            response = api_client.get('/events/1', headers={'X-User-Role': 'balvan'})

            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json() == {'detail': 'You must have a valid user role !'}

        def test_returns_404_and_error_message_if_getting_non_exists_event(self, api_client):
            response = api_client.get('/events/1')

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': 'Not Found'}

    class TestGetEvents:
        def test_return_200_and_future_events_with_available_tickets_when_no_filters_provided(
            self, api_client, pg_fake_events
        ):
            response = api_client.get('/events/')

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()
            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if event.event_datetime > datetime.now() and event.available_tickets > 0
            ]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('from_delta', 'to_delta'), [(1, 2), (3, 4), (2, 7)])
        def test_returns_200_and_filtered_events_by_date_range(self, api_client, pg_fake_events, from_delta, to_delta):
            now = datetime.now()
            datetime_from = now + timedelta(days=from_delta)
            datetime_to = now + timedelta(days=to_delta)

            response = api_client.get('/events/', params={'datetime_from': datetime_from, 'datetime_to': datetime_to})

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()
            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if datetime_from <= event.event_datetime <= datetime_to and event.available_tickets > 0
            ]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('page', 'items_count'), [(3, 2), (2, 3), (4, 1)])
        def test_returns_paginated_events(self, api_client, pg_fake_events, page, items_count):
            now = datetime.now()
            datetime_from = now + timedelta(days=1)
            datetime_to = now + timedelta(days=9)

            response = api_client.get(
                '/events/',
                params={
                    'datetime_from': datetime_from,
                    'datetime_to': datetime_to,
                    'page': page,
                    'items_count': items_count,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()

            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if datetime_from <= event.event_datetime <= datetime_to + timedelta(days=1)
                and event.available_tickets > 0
            ][(page - 1) * items_count : page * items_count]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('from_delta', 'to_delta'), [(5, 2), (10, 1)])
        def test_returns_400_if_invalid_date_range(self, api_client, from_delta, to_delta):
            now = datetime.now()
            datetime_from = now + timedelta(days=from_delta)
            datetime_to = now + timedelta(days=to_delta)

            response = api_client.get('/events/', params={'datetime_from': datetime_from, 'datetime_to': datetime_to})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json() == {'detail': 'datetime_from cannot be greater than datetime_to'}

        @pytest.mark.parametrize(
            ('date_param', 'error_message'),
            [
                ('datetime_from', 'datetime_from cannot be earlier than now'),
                ('datetime_to', 'datetime_to cannot be earlier than now'),
            ],
        )
        def test_returns_400_if_date_is_less_or_than_now(self, api_client, date_param, error_message):
            invalid_date = datetime.now() - timedelta(days=1)

            params = {date_param: invalid_date}
            response = api_client.get('/events/', params=params)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json() == {'detail': error_message}

        def test_returns_404_if_no_events_found(self, api_client):
            now = datetime.now()
            datetime_from = now + timedelta(days=100)
            datetime_to = now + timedelta(days=200)

            response = api_client.get('/events/', params={'datetime_from': datetime_from, 'datetime_to': datetime_to})

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': 'No events found'}

        def test_returns_422_if_extra_fields_provided(self, api_client):
            response = api_client.get('/events/', params={'extra_field': 'invalid'})

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert 'Extra inputs are not permitted' in response.json()['detail'][0]['msg']


class TestForAdminRouter:
    class TestPostEvent:
        def test_return_200_and_the_created_event_if_you_create_an_event(self, api_client, fake_event):
            fake_event['event_datetime'] = fake_event['event_datetime'].strftime('%Y-%m-%dT%H:%M')
            response = api_client.post('/events/', json=fake_event)
            assert response.status_code == status.HTTP_200_OK

            created_event = response.json()
            assert created_event.pop('id') == 1
            assert created_event.pop('deleted_at') is None
            assert created_event == fake_event

        @pytest.mark.parametrize(
            ('invalid_field', 'ivalid_value', 'error_message'),
            [
                ('name', None, 'Field required'),
                ('description', None, 'Field required'),
                ('event_datetime', '00-123-15:55', 'Input should be a valid datetime'),
                ('available_tickets', -1, 'Input should be greater than or equal to 0'),
                ('ticket_price', 0, 'Input should be greater than 0'),
            ],
        )
        def test_returns_422_if_invalid_data_provided(
            self, api_client, fake_event, invalid_field, ivalid_value, error_message
        ):
            fake_event['event_datetime'] = fake_event['event_datetime'].strftime('%Y-%m-%dT%H:%M')

            if ivalid_value is None:
                del fake_event[invalid_field]
            else:
                fake_event[invalid_field] = ivalid_value

            response = api_client.post('/events/', json=fake_event)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert error_message in response.text

        def test_returns_422_if_event_datetime_is_in_the_past(self, api_client, fake_event):
            fake_event['event_datetime'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
            response = api_client.post('/events/', json=fake_event)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert 'The datetime of the event cannot be the previous one' in response.text

    class TestDeleteEvent:
        async def test_return_200_and_event_deleted_if_you_delete_exists_event(self, api_client, pg_fake_events):
            event_for_delete_id = pg_fake_events[-1].id

            response = api_client.delete(f'/events/{event_for_delete_id}')
            assert response.status_code == status.HTTP_200_OK

            deleted_event = api_client.get(f'/events/{event_for_delete_id}').json()
            assert deleted_event['deleted_at'] is not None

        async def test_return_404_cant_delete_a_previously_deleted_event_again(self, api_client, pg_fake_events):
            event_for_delete_id = pg_fake_events[-1].id

            response = api_client.delete(f'/events/{event_for_delete_id}')
            assert response.status_code == status.HTTP_200_OK

            deleted_event = api_client.get(f'/events/{event_for_delete_id}').json()
            expected_deleted_at = deleted_event['deleted_at']

            response = api_client.delete(f'/events/{event_for_delete_id}')
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': [f'Invalid id {event_for_delete_id}']}

            re_deleted_event = api_client.get(f'/events/{event_for_delete_id}').json()
            assert re_deleted_event['deleted_at'] == expected_deleted_at

        def test_returns_404_if_deleting_non_existent_event(self, api_client):
            non_existent_id = 9999
            response = api_client.delete(f'/events/{non_existent_id}')
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': [f'Invalid id {non_existent_id}']}

    class TestUpdateEvent:
        async def test_returns_200_and_updated_event_if_update_successful(self, api_client, pg_fake_events):
            event_to_update = pg_fake_events[0]
            update_data = {
                'name': 'Updated Event Name',
                'description': 'Updated Event Description',
                'event_datetime': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
                'available_tickets': 50,
                'ticket_price': 1500.00,
            }
            response = api_client.put(f'/events/{event_to_update.id}', json=update_data)
            assert response.status_code == status.HTTP_200_OK
            updated_event = response.json()
            assert updated_event['name'] == update_data['name']
            assert updated_event['description'] == update_data['description']

        @pytest.mark.parametrize(
            ('invalid_field', 'ivalid_value', 'error_message'),
            [
                ('event_datetime', '00-123-15:55', 'Input should be a valid datetime'),
                ('available_tickets', -1, 'Input should be greater than or equal to 0'),
                ('ticket_price', 0, 'Input should be greater than 0'),
            ],
        )
        def test_returns_422_if_invalid_data_provided(
            self, api_client, pg_fake_events, invalid_field, ivalid_value, error_message
        ):
            event_to_update = pg_fake_events[0]
            update_data = {
                'name': 'Updated Event Name',
                'description': 'Updated Event Description',
                'event_datetime': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%dT%H:%M'),
                'available_tickets': 50,
                'ticket_price': 1500.00,
            }
            if ivalid_value is None:
                del update_data[invalid_field]
            else:
                update_data[invalid_field] = ivalid_value

            response = api_client.put(f'/events/{event_to_update.id}', json=update_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert error_message in response.text

        def test_returns_422_if_event_datetime_is_in_the_past(self, api_client, pg_fake_events):
            event_to_update = pg_fake_events[0]
            update_data = {
                'event_datetime': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            }
            response = api_client.put(f'/events/{event_to_update.id}', json=update_data)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert 'The datetime of the event cannot be the previous one' in response.text

        def test_returns_422_if_updating_event_without_all_fields(self, api_client, pg_fake_events):
            response = api_client.put(f'/events/{pg_fake_events[0].id}', json={})
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert 'At least one field must be provided for update' in response.text

        def test_returns_404_if_updating_non_existent_event(self, api_client, pg_fake_events):
            non_existent_id = 9999
            update_data = {'name': 'Updated Event Name'}
            response = api_client.put(f'/events/{non_existent_id}', json=update_data)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': [f'Invalid id {non_existent_id}']}

    def test_all_admin_endpoints_are_not_accessible_with_user_role(self, api_client):
        endpoints = [
            ('/events/', 'POST', {}),
            ('/events/1', 'DELETE', {}),
            ('/events/1', 'PUT', {}),
        ]
        for endpoint, method, body in endpoints:
            headers = {'X-User-Role': 'user'}
            if method == 'POST':
                response = api_client.post(endpoint, headers=headers, json=body)
            elif method == 'DELETE':
                response = api_client.delete(endpoint, headers=headers)
            elif method == 'PUT':
                response = api_client.put(endpoint, headers=headers, json=body)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert response.json() == {'detail': 'You must have a admin role !'}
