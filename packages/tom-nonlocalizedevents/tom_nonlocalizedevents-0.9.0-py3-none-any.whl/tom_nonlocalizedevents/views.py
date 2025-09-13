import json
import logging

from django.contrib import messages
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.views.generic.base import View
from django.urls import reverse
from django.conf import settings

from rest_framework import permissions, viewsets
from django_filters.rest_framework import DjangoFilterBackend

from tom_nonlocalizedevents.ingestion import ingest_sequence_from_hermes_message
from tom_nonlocalizedevents.models import EventCandidate, EventLocalization, NonLocalizedEvent
from tom_nonlocalizedevents.serializers import (EventCandidateSerializer, EventLocalizationSerializer,
                                                NonLocalizedEventSerializer)


logger = logging.getLogger(__name__)


class NonLocalizedEventListView(LoginRequiredMixin, ListView):
    """
    Unadorned Django ListView subclass for NonLocalizedEvent model.
    """
    model = NonLocalizedEvent
    template_name = 'tom_nonlocalizedevents/index.html'

    def get_queryset(self):
        # '-created' is most recent first
        qs = NonLocalizedEvent.objects.order_by('-created')
        return qs


# from the tom_alerts query_result.html
class CreateEventFromHermesAlertView(View):
    """
    Creates the models.NonLocalizedEvent instance and redirect to NonLocalizedEventDetailView
    """

    def post(self, request, *args, **kwargs):
        """
        """
        # the request.POST is a QueryDict object;
        query_id = self.request.POST['query_id']

        # events is a list[str] of NonLocalizedEvent event_id's: (e.g. 'MS230417a')
        # (i.e the selected events from the query result form)
        events = request.POST.getlist('events', [])

        # if the user didn't select an alert; warn and re-direct back
        if not events:
            messages.warning(request, 'Please select at least one Event to create.')
            reverse_url: str = reverse('tom_alerts:run', kwargs={'pk': query_id})
            return redirect(reverse_url)

        # Create NonLocalizedEvents for each of the selected events.
        for event_id in events:
            logger.debug(f'Creating event {event_id}...')
            # extract the Hermes event from the cache
            # (it was cached by tom_alerts.views.py::RunQueryView)
            cached_event = json.loads(cache.get(f'alert_{event_id}'))

            # early return: alert not in cache
            if not cached_event:
                messages.error(request, 'Could not createn event(s). Try re-running the query to refresh the cache.')
                return redirect(reverse('tom_alerts:run', kwargs={'pk': query_id}))

            # the NonLocalizedEvent is created by handling all the messages from
            # the event sequence as if they were ingested
            for sequenced_message in cached_event['sequences']:
                logger.debug(f"Creating sequence from HermesBroker: {sequenced_message}")
                ingest_sequence_from_hermes_message(sequenced_message)

        return redirect(reverse('nonlocalizedevents:index'))


#
# Django Rest Framework Views
#

class NonLocalizedEventViewSet(viewsets.ModelViewSet):
    """
    DRF API endpoint that allows NonLocalizedEvents to be viewed or edited.
    """
    queryset = NonLocalizedEvent.objects.all()
    serializer_class = NonLocalizedEventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_id', 'event_type']


class EventCandidateViewSet(viewsets.ModelViewSet):
    """
    DRF API endpoint for EventCandidate model.

    Implementation has changes for bulk_create and update/PATCH EventCandidate instances.
    """
    queryset = EventCandidate.objects.all()
    serializer_class = EventCandidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['nonlocalizedevent', 'viable', 'priority']

    def get_serializer(self, *args, **kwargs):
        # In order to ensure the list_serializer_class is used for bulk_create, we check that the POST data is a list
        # and add `many = True` to the kwargs
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Provide support for the PATCH HTTP verb to update individual model fields.

        An example request might look like:

            PATCH http://localhost:8000/api/eventcandidates/18/

        with a Request Body of:

            {
                "viability": false
            }

        """
        kwargs['partial'] = True
        return super().update(request, *args, **kwargs)


class EventLocalizationViewSet(viewsets.ModelViewSet):
    """
    DRF API endpoint that allows EventLocalizations to be viewed or edited.
    """
    queryset = EventLocalization.objects.all()
    serializer_class = EventLocalizationSerializer
    permission_classes = [permissions.IsAuthenticated]


class SupereventPkView(LoginRequiredMixin, TemplateView):
    template_name = 'tom_nonlocalizedevents/superevent_vue_app.html'

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        try:
            superevent = NonLocalizedEvent.objects.get(pk=kwargs['pk'])
            data = NonLocalizedEventSerializer(instance=superevent).data
            context['superevent_data'] = json.dumps(data)
            context['tom_api_url'] = settings.TOM_API_URL
            context['hermes_api_url'] = settings.HERMES_API_URL
            return context
        except NonLocalizedEvent.DoesNotExist:
            raise Http404


class SupereventIdView(LoginRequiredMixin, TemplateView):
    template_name = 'tom_nonlocalizedevents/superevent_vue_app.html'

    def get_context_data(self, **kwargs: dict) -> dict:
        context = super().get_context_data(**kwargs)
        try:
            superevent = NonLocalizedEvent.objects.get(event_id=kwargs['event_id'])
            data = NonLocalizedEventSerializer(instance=superevent).data
            context['superevent_data'] = json.dumps(data)
            context['tom_api_url'] = settings.TOM_API_URL
            context['hermes_api_url'] = settings.HERMES_API_URL
            return context
        except NonLocalizedEvent.DoesNotExist:
            raise Http404
