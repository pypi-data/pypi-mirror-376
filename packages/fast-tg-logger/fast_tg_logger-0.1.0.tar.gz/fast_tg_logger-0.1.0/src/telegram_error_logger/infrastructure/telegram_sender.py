import httpx

from ..interfaces.message_sender import MessageSender


class TelegramSender(MessageSender):
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id

    async def send_message(self, formatted_message: str) -> bool:
        url = f'https://api.telegram.org/bot{self.bot_token}/sendMessage'
        payload = {'chat_id': self.chat_id, 'text': formatted_message}
        try:
            timeout = httpx.Timeout(10)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200 and response.json().get('ok', False):
                    return True
                else:
                    return False
        except Exception:
            return False