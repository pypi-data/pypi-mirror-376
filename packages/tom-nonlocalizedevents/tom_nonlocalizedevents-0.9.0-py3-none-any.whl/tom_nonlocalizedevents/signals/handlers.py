from functools import partial

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import transaction

from tom_nonlocalizedevents.models import EventCandidate, EventLocalization
from tom_nonlocalizedevents.healpix_utils import update_all_credible_region_percents_for_candidates

import logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=EventCandidate)
def cb_post_save_event_candidate(sender, instance, created, **kwargs):
    # Anytime an EventCandidate is created, create and save its probability for different levels of credible region
    # for each localization we have for that event
    if created:
        logger.warning(f"Just created and saved new Event Candidate with healpix {instance.healpix}")
        localizations = instance.nonlocalizedevent.localizations.all()
        for localization in localizations:
            update_all_credible_region_percents_for_candidates(localization, [instance.pk])


@receiver(post_save, sender=EventLocalization)
def cb_post_save_event_localization(sender, instance, created, **kwargs):
    # Anytime a new EventLocalization is created, update the smallest probability credible region for each
    # EventCandidate associated with that nonlocalizedevent for the new localization
    if created:
        transaction.on_commit(
            partial(update_all_credible_region_percents_for_candidates, eventlocalization=instance)
        )
