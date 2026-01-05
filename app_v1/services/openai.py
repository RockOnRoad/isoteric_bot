import base64
import yaml
from pathlib import Path

from openai import AsyncOpenAI

from core.config import settings
from prompts import PROMPT_TEMPLATES
from services import calculate_arcana, ARCANA_MAP


class OpenAIClient:
    """Класс для работы с OpenAI API."""

    def __init__(
        self,
        api_key: str | None = None,
        conv: str | None = None,
        auto_create_conv: bool = False,
    ):
        """
        Инициализация клиента OpenAI.

        Args:
            api_key: API ключ OpenAI.
            conv: ID существующего разговора. Если не передан и auto_create_conv=True,
                  будет создан новый при первом вызове chatgpt_response.
            auto_create_conv: Если True, автоматически создавать conversation при первом
                             вызове chatgpt_response (если conv не передан).
                             Если False, conversation нужно передать явно.
        """
        self.client: AsyncOpenAI = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )
        self._conversation_id: str | None = conv
        self._auto_create_conv: bool = auto_create_conv

    async def get_models(self) -> list[str]:
        models = await self.client.models.list()
        return [model.id for model in models.data]

    async def _ensure_conversation(self) -> str:
        """
        Убедиться, что conversation существует. Если нет - создать новый.

        Returns:
            ID разговора.
        """
        if self._conversation_id is None:
            conversation = await self.client.conversations.create()
            self._conversation_id = conversation.id
        return self._conversation_id

    # async def chatgpt_response(
    #     self,
    #     prompt: str,
    #     *,
    #     model: str = "gpt-5.1-chat-latest",
    # ) -> tuple[str, str]:
    #     """
    #     Получить ответ от ChatGPT.

    #     Args:
    #         prompt: Текст запроса.
    #         model: Модель для использования. По умолчанию "gpt-5.1-chat-latest".

    #     Returns:
    #         Кортеж из (output_text, conversation_id).
    #     """
    #     # Используем сохраненный conversation_id или создаем новый, если разрешено
    #     if self._conversation_id:
    #         conversation_id = self._conversation_id
    #     elif self._auto_create_conv:
    #         conversation_id = await self._ensure_conversation()
    #     else:
    #         conversation_id = None

    #     response = await self.client.responses.create(
    #         model=model, input=prompt, conversation=conversation_id
    #     )
    #     return response.output_text, conversation_id

    async def chatgpt_response(
        self,
        feature: str,
        context: dict,
        *,
        model: str = "gpt-5.1-chat-latest",
    ) -> tuple[str, str]:
        """
        Получить ответ от ChatGPT.

        Args:
            feature: Тип генерации (first - первый ответ, readings - разборы, ...
            context: Контекст для генерации.
            model: Название модели для использования.

        Returns:
            Ответ от API с сгенерированным текстом.
        """
        # Используем сохраненный conversation_id или создаем новый, если разрешено
        if self._conversation_id:
            conversation_id = self._conversation_id
        elif self._auto_create_conv:
            conversation_id = await self._ensure_conversation()
        else:
            conversation_id = None

        #  Получаем данные из контекста
        name = context.get("name", "")
        sex = "male" if context.get("sex", "") == "m" else "female"
        birthday = context.get("birthday", "")

        arcanas: dict = calculate_arcana(birthday)
        main_arcana = arcanas["main_arcana"]
        main_arcana_name = ARCANA_MAP[main_arcana]
        day_arcana = arcanas["day_arcana"]
        day_arcana_name = ARCANA_MAP[day_arcana]

        domain = context.get("domain", "")
        aspect = context.get("aspect", "")

        #  Собираем промпт для "readings" (или "witch")
        if feature == "readings":
            #  Специально для reading-ов подгружаем данные из YAML файла
            yaml_path = Path(__file__).parent.parent / "schemas" / "readings_map.yml"
            with open(yaml_path, "r", encoding="utf-8") as f:
                readings_data = yaml.safe_load(f)
            #  Получаем специальную часть prompt-а для reading-ов
            special = readings_data[domain]["buttons"][aspect]["special"]
            aspect_name = readings_data[domain]["buttons"][aspect]["label"]
            #  Собираем промпт для reading-ов
            bio = PROMPT_TEMPLATES["readings_context"].render(
                name=name,
                sex=sex,
                birthday=birthday,
                main_arcana=main_arcana,
                main_arcana_name=main_arcana_name,
                domain=domain,
                aspect=aspect_name,
            )
            prompt: str = PROMPT_TEMPLATES["readings_base"].render(
                special=special,
                context=bio,
                name=name,
                main_arcana=main_arcana,
                main_arcana_name=main_arcana_name,
                aspect=aspect_name,
            )
            print(prompt)

        elif feature == "first":
            bio = PROMPT_TEMPLATES["first_text_context"].render(
                name=name,
                sex=sex,
                birthday=birthday,
                day_arcana=day_arcana,
                day_arcana_name=day_arcana_name,
            )
            prompt: str = PROMPT_TEMPLATES["first_text_base"].render(
                name=name,
                arcana=day_arcana,
                arcana_name=day_arcana_name,
                context=bio,
            )
            # print(prompt)

        response = await self.client.responses.create(
            model=model, input=prompt, conversation=conversation_id
        )
        return response.output_text, conversation_id

    async def chatgpt_response_follow_up(
        self,
        prompt: str,
        *,
        model: str = "gpt-5.1-chat-latest",
    ):
        response = await self.client.responses.create(
            model=model, input=prompt, conversation=self._conversation_id
        )
        return response.output_text

    async def chatgpt_image(
        self,
        prompt: str,
        *,
        model: str = "gpt-image-1",
        # reference_image_url: str | None = "https://ibb.co/r2DBGvdh",
        # reference_image_url: str | None = "https://i.ibb.co/zVq3hN6g/owl-pic-620-6b3d4bb80adc24b34ad43895d6d7ae8e.jpg",
    ):
        result = await self.client.images.edit(
            model=model,
            image=[
                open(
                    "app_v1/src/assets/owl_pic_620_6b3d4bb80adc24b34ad43895d6d7ae8e.jpg",
                    "rb",
                ),
            ],
            prompt=prompt,
            input_fidelity="high",
        )

        image_base64 = await result.data[0].b64_json
        image_bytes = base64.b64decode(image_base64)

        return image_bytes


# Создаем экземпляр по умолчанию для обратной совместимости
# client_instance = OpenAIClient()

# Экспортируем для обратной совместимости
# client = client_instance.client
# chatgpt_response = client_instance.chatgpt_response
