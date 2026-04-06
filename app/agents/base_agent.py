import instructor
from openai import AsyncOpenAI
from app.core.infra.llm_router import LLMRouter

class BaseAgent:
    def __init__(self, client: AsyncOpenAI, router: LLMRouter):
        # 使用 instructor 增强客户端，使其支持 response_model 参数
        self.client = instructor.from_openai(client)
        self.router = router

    async def call_llm(self, role, content, response_model, system_prompt):
        model = self.router.get_model(role, len(content))
        return await self.client.chat.completions.create(
            model=model,
            response_model=response_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ],
            max_retries=3
        )
