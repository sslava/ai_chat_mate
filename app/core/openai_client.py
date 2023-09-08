from baski import clients

__all__ = ['OpenAiClient']


class OpenAiClient(clients.OpenAiClient):

    def __init__(self, api_key):
        super().__init__(api_key=api_key, system_prompt=system_prompt_assistant, user_prompts=prompts, chunk_length=256)

    def continue_chat(self, user_id, history, message):
        return self.from_prompt(user_id, 'continue_chat', history=history, message=message)


system_prompt_assistant = """
You are the  helpful, creative, joyful, friendly, trustworthy assistant
""".strip()


prompts = {
    "continue_chat": {
        "model": "gpt-3.5-turbo",
        "prompt": "{message}",
        "temperature": 1.1
    }
}
