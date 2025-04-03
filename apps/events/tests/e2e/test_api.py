from datetime import date, timedelta

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
        def test_return_200_and_tomorrows_events_with_available_tickets_when_no_filters_provided(
            self, api_client, pg_fake_events
        ):
            response = api_client.get('/events/')

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()
            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if event.event_date == date.today() + timedelta(days=1) and event.available_tickets > 0
            ]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('from_delta', 'to_delta'), [(1, 2), (3, 4), (2, 7)])
        def test_returns_200_and_filtered_events_by_date_range(self, api_client, pg_fake_events, from_delta, to_delta):
            today = date.today()
            date_from = today + timedelta(days=from_delta)
            date_to = today + timedelta(days=to_delta)

            response = api_client.get('/events/', params={'date_from': date_from, 'date_to': date_to})

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()
            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if date_from <= event.event_date <= date_to and event.available_tickets > 0
            ]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('page', 'items_count'), [(3, 2), (2, 3), (4, 1)])
        def test_returns_paginated_events(self, api_client, pg_fake_events, page, items_count):
            today = date.today()
            date_from = today + timedelta(days=1)
            date_to = today + timedelta(days=9)

            response = api_client.get(
                '/events/',
                params={'date_from': date_from, 'date_to': date_to, 'page': page, 'items_count': items_count},
            )

            assert response.status_code == status.HTTP_200_OK

            returned_events = response.json()

            expected_events = [
                event.model_dump(mode='json')
                for event in pg_fake_events
                if date_from <= event.event_date <= date_to + timedelta(days=1) and event.available_tickets > 0
            ][(page - 1) * items_count : page * items_count]

            assert returned_events == expected_events

        @pytest.mark.parametrize(('from_delta', 'to_delta'), [(5, 2), (10, 1)])
        def test_returns_400_if_invalid_date_range(self, api_client, from_delta, to_delta):
            today = date.today()
            date_from = today + timedelta(days=from_delta)
            date_to = today + timedelta(days=to_delta)

            response = api_client.get('/events/', params={'date_from': date_from, 'date_to': date_to})

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json() == {'detail': 'date_from cannot be greater than date_to'}

        @pytest.mark.parametrize(
            ('date_param', 'error_message'),
            [
                ('date_from', 'date_from cannot be earlier than tomorrow'),
                ('date_to', 'date_to cannot be earlier than tomorrow'),
            ],
        )
        def test_returns_400_if_date_is_less_than_tomorrow(self, api_client, date_param, error_message):
            invalid_date = date.today()

            params = {date_param: invalid_date}
            response = api_client.get('/events/', params=params)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.json() == {'detail': error_message}

        def test_returns_404_if_no_events_found(self, api_client):
            today = date.today()
            date_from = today + timedelta(days=100)
            date_to = today + timedelta(days=200)

            response = api_client.get('/events/', params={'date_from': date_from, 'date_to': date_to})

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert response.json() == {'detail': 'No events found'}

        def test_returns_422_if_extra_fields_provided(self, api_client):
            response = api_client.get('/events/', params={'extra_field': 'invalid'})

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert 'Extra inputs are not permitted' in response.json()['detail'][0]['msg']
