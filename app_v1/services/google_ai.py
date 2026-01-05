from io import BytesIO
import yaml
from pathlib import Path

from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile
from google.genai import Client
from google.genai.types import GenerateContentConfig, ImageConfig

from core.config import settings
from prompts import PROMPT_TEMPLATES
from services import ARCANA_MAP, calculate_arcana


class GoogleAI:
    """Сервис для работы с Google Gemini API."""

    def __init__(self, api_key: str | None = None):
        self.client: Client = Client(api_key=settings.google_api_key)

    # def generate_content(
    #     self,
    #     model: str = "gemini-2.5-flash-image",
    #     contents: str | list = "",
    # ):
    #     """
    #     Генерирует контент с помощью модели Gemini.

    #     Args:
    #         model: Название модели для использования.
    #         contents: Текст или список содержимого для генерации.

    #     Returns:
    #         Ответ от API с сгенерированным контентом.
    #     """

    #     config = GenerateContentConfig(
    #         response_modalities=["IMAGE"],
    #         image_config=ImageConfig(
    #             aspect_ratio="16:9",
    #         ),
    #     )

    #     return self.client.models.generate_content(
    #         model=model,
    #         contents=contents,
    #         config=config,
    #     )

    async def generate_picture(
        self,
        feature: str,
        context: dict,
        state: FSMContext,
        *,
        model: str = "gemini-2.5-flash-image",
    ) -> BufferedInputFile | None:
        """
        Генерирует изображение с помощью модели Gemini.

        Args:
            feature: Тип генерации (first - первое изображение, ...
            context: Контекст для генерации.
            model: Название модели для использования.

        Returns:
            Ответ от API с сгенерированным изображением.
        """

        name = context.get("name", "")
        sex = "male" if context.get("sex", "") == "m" else "female"
        birthday = context.get("birthday", "")
        domain = context.get("domain", "")
        another_birthday = context.get("another_birthday", None)

        arcanas: dict = calculate_arcana(birthday)
        main_arcana = arcanas["main_arcana"]
        main_arcana_name = ARCANA_MAP[main_arcana]
        day_arcana = arcanas["day_arcana"]
        day_arcana_name = ARCANA_MAP[day_arcana]

        if sex == "male":
            gender_guide = "Male archetype, age 30-60, calm stability, grounded confidence, no aggression, no dominance."
        else:
            gender_guide = "Female archetype, age 25-55, soft confidence, inner strength, non-glamour, non-sexualized."

        if feature == "first":
            #  Собираем промпт
            context = PROMPT_TEMPLATES["first_image_context"].render(
                arcana_number=day_arcana,
                arcana_name=day_arcana_name,
                name=name,
                sex=sex,
            )
            prompt = PROMPT_TEMPLATES["first_image_base"].render(
                context=context,
                gender_guide=gender_guide,
            )

        elif feature == "ai_portraits":
            #  Подгружаем специфику портрета по домену
            yaml_path = (
                Path(__file__).parent.parent / "schemas" / "ai_portraits_map.yml"
            )
            with open(yaml_path, "r", encoding="utf-8") as f:
                ai_portraits_data = yaml.safe_load(f)

            prompt_focus = ai_portraits_data[domain]["prompt_focus"]

            #  Собираем промпт
            context = PROMPT_TEMPLATES["ai_portraits_image_context"].render(
                arcana_number=main_arcana,
                arcana_name=main_arcana_name,
                name=name,
                sex=sex,
                birthday=birthday,
            )
            if another_birthday:
                another_arcanas = calculate_arcana(another_birthday)
                another_main_arcana = another_arcanas["main_arcana"]
                context = f'{context}\nPartners Arcanum: {another_main_arcana} "{ARCANA_MAP[another_main_arcana]}"'
            prompt = PROMPT_TEMPLATES["ai_portraits_image_base"].render(
                context=context,
                gender_guide=gender_guide,
                prompt_focus=prompt_focus,
            )
            await state.clear()

        config = GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=ImageConfig(
                aspect_ratio="16:9",
            ),
        )

        response = self.client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )
        for part in response.parts:
            if part.inline_data:
                # Получаем байты изображения напрямую из inline_data
                img_bytes: BytesIO = BytesIO(part.inline_data.data)
                img_bytes.seek(0)

                photo: BufferedInputFile = BufferedInputFile(
                    img_bytes.getvalue(), filename="portrait.jpg"
                )
                return photo
        return None

    async def google_models(self) -> list[str]:
        """
        Получает список доступных моделей Gemini.

        Returns:
            Список доступных моделей Gemini.
        """
        models = self.client.models.list()
        # return [model.name for model in models]
        return models
