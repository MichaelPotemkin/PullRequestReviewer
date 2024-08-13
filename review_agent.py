from langchain.schema import HumanMessage, SystemMessage
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_openai import ChatOpenAI

from config import settings
from prompts import SYSTEM_PROMPT
from schemas import Difference


class BaseReviewer:
    def get_response(self, user_input: str) -> str:
        raise NotImplementedError

    def review_diff(self, difference: Difference) -> Difference:
        user_input = (
            f"File: {difference.file}\n"
            f"Change type: {difference.change_type}\n"
            f"Diff:\n{difference.diff}"
        )

        response = self.get_response(user_input)

        if response.lower().strip(" .") == "none":
            return difference
        return difference.model_copy(update={"comment": response})

    def review_diffs(self, differences: list[Difference]) -> list[Difference]:
        return [self.review_diff(diff) for diff in differences]


class MistralReviewer(BaseReviewer):
    MODEL_NAME = "mistral-large-latest"

    def __init__(self):
        if not settings.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY is not set")
        self.llm = ChatMistralAI(api_key=settings.MISTRAL_API_KEY, model=self.MODEL_NAME)

    def get_response(self, user_input: str) -> str:
        try:
            response = self.llm([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_input)
            ])
            return response.content
        except Exception as e:
            return f"An error occurred: {e}"


class OpenAIReviewer(BaseReviewer):
    MODEL_NAME = "gpt-4-turbo"

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set")
        self.llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model_name=self.MODEL_NAME)

    def get_response(self, user_input: str) -> str:
        try:
            response = self.llm.invoke([
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=user_input)
            ])
            return response.content
        except Exception as e:
            return f"An error occurred: {e}"
