"""
Test result handling.

"""
from hamcrest import (
    assert_that,
    has_properties,
)

from microcosm_pubsub.errors import Nack, SkipMessage
from microcosm_pubsub.message import SQSMessage
from microcosm_pubsub.result import MessageHandlingResult, MessageHandlingResultType
from microcosm_pubsub.tests.fixtures import DerivedSchema, ExampleDaemon


MESSAGE_ID = "message-id"
RECEIPT_HANDLE = "receipt-handle"


class TestMessageHandlingResult:

    def setup(self):
        self.graph = ExampleDaemon.create_for_testing().graph
        self.message = SQSMessage(
            consumer=self.graph.sqs_consumer,
            content=None,
            media_type=DerivedSchema.MEDIA_TYPE,
            message_id=MESSAGE_ID,
            receipt_handle=RECEIPT_HANDLE,
        )
        self.graph.sqs_consumer.sqs_client.reset_mock()

    def test_succeeded_truthy(self):
        def func(message):
            return True

        result = MessageHandlingResult.invoke(
            func=func,
            message=self.message,
        )

        assert_that(
            result,
            has_properties(
                media_type="application/vnd.microcosm.derived",
                result=MessageHandlingResultType.SUCCEEDED,
            ),
        )
        # ack
        self.graph.sqs_consumer.sqs_client.delete_message.assert_called_with(
            QueueUrl="queue",
            ReceiptHandle=RECEIPT_HANDLE,
        )

    def test_skipped_falsey(self):
        def func(message):
            return False

        result = MessageHandlingResult.invoke(
            func=func,
            message=self.message,
        )

        assert_that(
            result,
            has_properties(
                media_type="application/vnd.microcosm.derived",
                result=MessageHandlingResultType.SKIPPED,
            ),
        )
        # ack
        self.graph.sqs_consumer.sqs_client.delete_message.assert_called_with(
            QueueUrl="queue",
            ReceiptHandle=RECEIPT_HANDLE,
        )

    def test_skipped_exception(self):
        def func(message):
            raise SkipMessage("ignorance is bliss")

        result = MessageHandlingResult.invoke(
            func=func,
            message=self.message,
        )

        assert_that(
            result,
            has_properties(
                media_type="application/vnd.microcosm.derived",
                result=MessageHandlingResultType.SKIPPED,
            ),
        )
        # ack
        self.graph.sqs_consumer.sqs_client.delete_message.assert_called_with(
            QueueUrl="queue",
            ReceiptHandle=RECEIPT_HANDLE,
        )

    def test_retried_nack(self):
        def func(message):
            raise Nack(3)

        result = MessageHandlingResult.invoke(
            func=func,
            message=self.message,
        )

        assert_that(
            result,
            has_properties(
                media_type="application/vnd.microcosm.derived",
                result=MessageHandlingResultType.RETRIED,
            ),
        )
        # nack with custom retry visibility timeout
        self.graph.sqs_consumer.sqs_client.change_message_visibility.assert_called_with(
            QueueUrl="queue",
            ReceiptHandle=RECEIPT_HANDLE,
            VisibilityTimeout=3,
        )

    def test_failed_exception(self):
        def func(message):
            raise Exception("FAIL")

        result = MessageHandlingResult.invoke(
            func=func,
            message=self.message,
        )

        assert_that(
            result,
            has_properties(
                media_type="application/vnd.microcosm.derived",
                result=MessageHandlingResultType.FAILED,
            ),
        )
        # nack with default retry visibility timeout
        self.graph.sqs_consumer.sqs_client.change_message_visibility.assert_called_with(
            QueueUrl="queue",
            ReceiptHandle=RECEIPT_HANDLE,
            VisibilityTimeout=5,
        )
