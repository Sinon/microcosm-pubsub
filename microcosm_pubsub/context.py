"""
Message context.

"""
from typing import Dict

from microcosm.api import defaults, typed
from microcosm.config.types import boolean
from microcosm_logging.decorators import logger

from microcosm_pubsub.constants import TTL_KEY, URI_KEY
from microcosm_pubsub.message import SQSMessage


@defaults(
    enable_ttl=typed(boolean, default_value=True),
    initial_ttl=typed(int, default_value=32),
)
@logger
class SQSMessageContext:
    """
    Factory for per-message contexts.

    """
    def __init__(self, graph):
        self.enable_ttl = graph.config.sqs_message_context.enable_ttl
        self.initial_ttl = graph.config.sqs_message_context.initial_ttl

    def __call__(self, context, **kwargs) -> Dict[str, str]:
        """
        Create a new context from a message.

        """
        if isinstance(context, SQSMessage):
            return self.from_sqs_message(context, **kwargs)

        # XXX we want to remove this
        return self.from_dict(context, **kwargs)

    def from_sqs_message(self, message, **kwargs):
        context = dict(
            # include the message id
            message_id=message.message_id,
            # include
            **message.opaque_data,
            **kwargs,
        )

        # include the TTL (if enabled)
        if self.enable_ttl:
            ttl = message.ttl if message.ttl is not None else self.initial_ttl
            context[TTL_KEY] = str(ttl - 1)

        # include the URI (if there is one)
        if message.uri:
            context[URI_KEY] = message.uri

        return context

    def from_dict(self, dct, **kwargs):
        return dict(
            **dct.get("opaque_data", {}),
            **kwargs,
        )
