"""Independent maintenance stages; failure in one cannot skip the other."""
import logging

logger = logging.getLogger(__name__)


def maintain_knowledge(engine):
    from .document_tools import DocumentTools
    outcomes = {}
    operations = (
        ('queue', lambda: DocumentTools(engine, operator=True).resume_queued()),
        ('inbox', engine.scan_knowledge_watch),
    )
    for name, operation in operations:
        try:
            operation()
            outcomes[name] = 'SUCCEEDED'
        except Exception as error:
            # Source paths/text may be present in exceptions; log fixed scope/type.
            logger.warning('Knowledge maintenance failed: stage=%s error_type=%s', name, type(error).__name__)
            outcomes[name] = 'FAILED'
    return outcomes
