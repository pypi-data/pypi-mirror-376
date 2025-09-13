from ..entities.error_message import ErrorMessage
from ..interfaces.error_formatter import ErrorFormatter
from ..interfaces.message_sender import MessageSender


class LogError:
    def __init__(self, sender: MessageSender, formatter: ErrorFormatter):
        self.sender = sender
        self.formatter = formatter

    async def execute(self, message: ErrorMessage) -> bool:
        formatted_message = self.formatter.format_message(message)
        success = await self.sender.send_message(formatted_message)
        return success
