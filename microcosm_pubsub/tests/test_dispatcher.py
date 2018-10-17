"""
Dispatcher tests.

"""
from hamcrest import (
    assert_that,
    greater_than,
    has_properties,
)

from microcosm_pubsub.conventions import created
from microcosm_pubsub.message import SQSMessage
from microcosm_pubsub.result import MessageHandlingResultType
from microcosm_pubsub.tests.fixtures import (
    ExampleDaemon,
    DerivedSchema,
)


MESSAGE_ID = "message-id"


class TestDispatcher:

    def setup(self):
        self.daemon = ExampleDaemon.create_for_testing()
        self.graph = self.daemon.graph

        self.dispatcher = self.graph.sqs_message_dispatcher

        self.content = dict(bar="baz", uri="http://example.com")
        self.message = SQSMessage(
            consumer=self.graph.sqs_consumer,
            content=self.content,
            media_type=DerivedSchema.MEDIA_TYPE,
            message_id=MESSAGE_ID,
            receipt_handle=None,
        )
        self.graph.sqs_consumer.sqs_client.reset_mock()

    def test_handle_message_succeeded(self):
        result = self.dispatcher.handle_message(
            message=self.message,
            bound_handlers=self.daemon.bound_handlers,
        )
        assert_that(
            result,
            has_properties(
                elapsed_time=greater_than(0.0),
                result=MessageHandlingResultType.SUCCEEDED,
            ),
        )

    def test_handle_message_ignored(self):
        """
        Unsupported media types are ignored.

        """
        self.message.media_type = created("bar")
        assert_that(
            self.dispatcher.handle_message(
                message=self.message,
                bound_handlers=self.daemon.bound_handlers,
            ),
            has_properties(
                elapsed_time=greater_than(0.0),
                result=MessageHandlingResultType.IGNORED,
            ),
        )

    def test_handle_message_expired(self):
        """
        Unsupported media types are ignored.

        """
        self.message.content = dict(
            opaque_data={
                "X-Request-Ttl": "0",
            },
        )
        assert_that(
            self.dispatcher.handle_message(
                message=self.message,
                bound_handlers=self.daemon.bound_handlers,
            ),
            has_properties(
                elapsed_time=greater_than(0.0),
                result=MessageHandlingResultType.EXPIRED,
            ),
        )
