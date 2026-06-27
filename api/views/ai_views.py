import os
import json
import logging
from datetime import datetime
from typing import Optional
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
import requests

logger = logging.getLogger(__name__)

# Ordered list of models to try for Grok
GROK_MODEL_FALLBACKS = [
    "grok-3",
    "grok-3-fast",
    "grok-2",
    "grok-beta",
]

# Ordered list of models to try for GLM / Zhipu
GLM_MODEL_FALLBACKS = [
    "glm-5-turbo",
    "glm-5.2",
    "glm-5.1",
    "glm-5",
    "glm-4.7",
    "glm-4.6",
    "glm-4.5-air",
    "glm-4.5",
]

from ..utils import ApiResponse


from django.db.models import Sum
from ..models import Expense


class AIAssistantView(APIView):
    """
    POST /api/v1/ai/assistant
    Accepts `text`, `audio`, `image`, and `history`.
    """
    permission_classes = []
    authentication_classes = []
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request):
        # 1. Gather API configurations
        grok_key = os.environ.get("GROK_API_KEY") or os.environ.get("XAI_API_KEY")
        glm_key = os.environ.get("GLM_API_KEY") or os.environ.get("ZHIPUAI_API_KEY")

        if not grok_key and not glm_key:
            return ApiResponse.success(
                data={
                    "message": "AI assistant is not configured yet. Please add GROK_API_KEY or GLM_API_KEY to your environment/dotenv file.",
                    "action": None,
                },
                message="AI service not configured",
                status_code=503,
            )

        text = request.data.get('text')
        audio_file = request.FILES.get('audio')
        image_file = request.FILES.get('image')
        history_str = request.data.get('history')
        if not text and not audio_file and not image_file:
            return ApiResponse.error("Please provide 'text', 'audio', or 'image' input.", 400)

        # Parse history
        try:
            history = json.loads(history_str) if history_str else []
        except:
            history = []

        # Define tools that close over the current user
        user = request.user
        if not user or not user.is_authenticated:
            # Fallback to first user for demo purposes if not logged in
            from django.contrib.auth.models import User
            user = User.objects.first()

        def find_expense(query: str) -> str:
            """Searches the user's database for recent expenses matching the query (e.g., 'coffee', 'grocery', 'uber')."""
            expenses = Expense.objects.filter(user=user, title__icontains=query).order_by('-expense_date')[:5]
            if not expenses.exists():
                return json.dumps({"status": "no expenses found matching query"})
            
            results = []
            for e in expenses:
                results.append({
                    "id": e.id,
                    "title": e.title,
                    "amount": float(e.amount),
                    "category": e.category,
                    "date": e.expense_date.isoformat()
                })
            return json.dumps({"status": "found", "results": results})

        def get_monthly_summary(month: int, year: int) -> str:
            """Gets the user's total spending and highest category for a specific month and year."""
            expenses = Expense.objects.filter(user=user, expense_date__month=month, expense_date__year=year)
            total = expenses.aggregate(total=Sum('amount'))['total'] or 0
            return json.dumps({"total_spent": float(total), "month": month, "year": year, "count": expenses.count()})

        system_instruction = (
            "You are an intelligent expense tracker assistant. "
            "You can answer questions about the user's spending using the provided tools, or help them manage expenses. "
            "IMPORTANT: When the user wants to ADD, UPDATE, or DELETE an expense, you MUST output an 'action' payload so the frontend can show a confirmation card. "
            "If they ask to update/delete, use the find_expense tool FIRST to get the correct ID, then output the action. "
            f"The current date and time is {datetime.now().isoformat()}. "
            "Always respond conversationally in the 'message' field."
        )

        try:
            messages = [
                {"role": "system", "content": system_instruction},
            ]

            for msg in history:
                role = msg.get('role', 'user')
                if role == 'model':
                    role = 'assistant'
                elif role not in ['user', 'assistant']:
                    role = 'user'

                parts = msg.get('parts', '')
                if isinstance(parts, list):
                    text_content = ' '.join(str(p) for p in parts if p)
                else:
                    text_content = str(parts)

                messages.append({"role": role, "content": text_content})

            if audio_file or image_file:
                prompt = text or "Analyze the uploaded media for expense-related information."
                if audio_file:
                    prompt += f"\nAudio file: {audio_file.name}"
                if image_file:
                    prompt += f"\nImage file: {image_file.name}"
            else:
                prompt = text or ""

            messages.append({"role": "user", "content": prompt})

            response = None
            last_error = None

            # 2. Determine which provider to use. Prioritize GLM if key is present, fallback to Grok.
            if glm_key:
                api_base_url = os.environ.get("GLM_API_BASE_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
                env_model = os.environ.get("GLM_MODEL")
                models_to_try = [env_model] if env_model else GLM_MODEL_FALLBACKS
                
                for model_name in models_to_try:
                    try:
                        logger.info(f"Trying GLM model: {model_name}")
                        resp = requests.post(
                            api_base_url,
                            headers={
                                "Authorization": f"Bearer {glm_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_name,
                                "messages": messages,
                                "temperature": 0.2,
                            },
                            timeout=60,
                        )
                        if resp.status_code == 400:
                            logger.warning(f"GLM model '{model_name}' returned 400. Body: {resp.text}")
                            last_error = f"400 from GLM model '{model_name}': {resp.text}"
                            continue
                        resp.raise_for_status()
                        response = resp
                        break
                    except Exception as err:
                        logger.warning(f"GLM model '{model_name}' failed: {err}")
                        last_error = str(err)
                        continue

            elif grok_key:
                api_base_url = os.environ.get("GROK_API_BASE_URL", "https://api.x.ai/v1/chat/completions")
                env_model = os.environ.get("GROK_MODEL")
                models_to_try = [env_model] if env_model else GROK_MODEL_FALLBACKS

                for model_name in models_to_try:
                    try:
                        logger.info(f"Trying Grok model: {model_name}")
                        resp = requests.post(
                            api_base_url,
                            headers={
                                "Authorization": f"Bearer {grok_key}",
                                "Content-Type": "application/json",
                            },
                            json={
                                "model": model_name,
                                "messages": messages,
                                "temperature": 0.2,
                            },
                            timeout=60,
                        )
                        if resp.status_code == 400:
                            logger.warning(f"Grok model '{model_name}' returned 400. Body: {resp.text}")
                            last_error = f"400 from Grok model '{model_name}': {resp.text}"
                            continue
                        resp.raise_for_status()
                        response = resp
                        break
                    except Exception as err:
                        logger.warning(f"Grok model '{model_name}' failed: {err}")
                        last_error = str(err)
                        continue

            if response is None:
                logger.error(f"AI Assistant call failed. Last error: {last_error}")
                return ApiResponse.error(
                    message=f"AI service unavailable. Last error: {last_error}",
                    status_code=503,
                )

            payload = response.json()
            content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            if isinstance(content, list):
                content = " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))

            # Smart parsing of JSON content to extract message and action
            parsed_data = {
                "message": content or "No response from AI.",
                "action": None,
            }

            if content:
                content_stripped = content.strip()
                if content_stripped.startswith("```json"):
                    content_stripped = content_stripped[7:]
                if content_stripped.endswith("```"):
                    content_stripped = content_stripped[:-3]
                content_stripped = content_stripped.strip()

                try:
                    json_data = json.loads(content_stripped)
                    if isinstance(json_data, dict):
                        parsed_data["message"] = json_data.get("message", content)
                        parsed_data["action"] = json_data.get("action", None)
                except:
                    pass

            return ApiResponse.success(
                data=parsed_data,
                message="AI responded successfully"
            )

        except Exception as e:
            logger.exception("Unexpected error in AI assistant view")
            return ApiResponse.error(
                message=f"AI processing failed: {str(e)}",
                status_code=500,
            )
