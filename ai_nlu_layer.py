# ai_nlu_layer.py

import openai
import json
import os
from questionnaire_data import QUESTIONNAIRE_STRUCTURE

class AINLULayer:
    def __init__(self, model="gpt-3.5-turbo", api_key=None):
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API Key not found. Please set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.question_structure = QUESTIONNAIRE_STRUCTURE

    def _get_question_schema_for_llm(self, questions_to_consider: list) -> str:
        schema_parts = []
        for q in questions_to_consider:
            q_id = q["id"]
            q_type = q["type"]
            q_options = ", ".join(q["options"]) if q_type == "select" else ""
            q_mapping_context = q.get("mapping_context", q["question"])
            schema_parts.append(f"""
            - {q_id} (類型: {q_type}): {q_mapping_context} {f"可選值: [{q_options}]" if q_options else ""}""")
        return "\n".join(schema_parts)

    def parse_chat_response_to_answers(self, user_input: str, all_questions: list, current_answers: dict, chat_history: list = None) -> dict:
        questions_schema = self._get_question_schema_for_llm(all_questions)
        system_prompt = f"""
        你是一個智能問卷調查AI助理，專門從使用者的自然語言回答中，盡可能地提取出問卷中所有相關的答案。
        你的目標是精確地識別使用者提供的資訊，並將其映射到問卷問題的 'id' 上。

        請輸出一個 JSON 格式的物件，包含以下鍵：
        - "extracted_answers": 一個字典，鍵是問卷問題的 'id'，值是從使用者輸入中提取出的答案。
                               如果某個問題在使用者輸入中沒有明確提及或無法以高置信度提取，請不要包含該鍵，或將其值設為 null。
                               對於 'boolean' 類型，請務必轉換為 '是' 或 '否'。
                               對於 'select' 類型，請務必選擇最接近的選項。
                               對於 'number' 類型，請提取數字。
                               對於開放式文本問題（如 feedback_comments, detailed_dissatisfaction_reason），請提取相關的完整意見。
        - "action_request": 字符串，指示下一步操作。
                            - "continue_questionnaire": 意味著你提取了部分或所有答案，且對話應繼續。
                            - "finish_questionnaire": 只有當使用者明確說出例如「結束問卷」、「完成問卷」、「結束」、「完成」、「不想填了」等明確的結束指令時，才設為此值。避免將簡短回答或抱怨誤判為結束。
                            - "no_change": 意味著使用者輸入與問卷問題無關，或沒有新的可提取信息。
        - "reasoning": 字符串，簡要說明你的提取結果和下一步的建議。

        請注意：
        - 只有在使用者明確提及或回答相關問題時才提取答案。避免產生幻覺或推斷。
        - 如果使用者一次提供了多個問題的答案，請盡可能全部提取。
        - 如果使用者明確表示要修改之前給出的答案，請在 `extracted_answers` 中提供該問題的新答案。
        - 你的回答必須僅包含 JSON。

        問卷問題列表 (及其映射上下文):
        {questions_schema}

        目前已收集的答案 (如果使用者提及修改，請參考這些舊答案):
        {json.dumps(current_answers, ensure_ascii=False)}
        """
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-8:])
        messages.append({"role": "user", "content": f"這是我的回答：{user_input}"})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            response_content = response.choices[0].message.content
            parsed_output = json.loads(response_content)
            if not all(k in parsed_output for k in ["extracted_answers", "action_request"]):
                raise ValueError("LLM response missing required keys.")
            return parsed_output
        except json.JSONDecodeError as e:
            print(f"錯誤：LLM 返回的內容不是有效的 JSON: {e}\n原始響應內容: {response_content}")
            return {"extracted_answers": {}, "action_request": "error", "reasoning": f"Invalid JSON from LLM: {e}"}
        except Exception as e:
            print(f"與 OpenAI 互動時發生錯誤: {e}")
            return {"extracted_answers": {}, "action_request": "error", "reasoning": f"OpenAI API error: {e}"}

    def generate_initial_greeting_and_guidance(self) -> str:
        first_required_question = next((q for q in self.question_structure if q.get("validation_rule") == "required"), None)
        initial_prompt_part = ""
        if first_required_question:
            initial_prompt_part = f"我們可以從您的「{first_required_question['question'].replace('？', '')}」開始嗎？"
        else:
            initial_prompt_part = "您準備好了嗎？有什麼想先告訴我的嗎？隨時開始吧！"

        system_prompt = f"""
        你是一個友善的問卷AI助理。請生成一段簡短的歡迎語，並簡要介紹問卷的靈活填寫方式。
        請提示使用者可以一次提供多個答案，可以隨時修改之前的答案，並且可以說「結束」來完成問卷。
        最後，以一個具體的問題或邀請結束，引導使用者開始提供資訊。
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": f"生成初始歡迎語和指南，並引導開始。引導語應包含：「{initial_prompt_part}」"})
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"生成歡迎語時發生錯誤: {e}")
            return "--- 歡迎來到我們的智能問卷調查！ --- 請開始提供您的資訊。"

    def generate_next_questions_prompt(self, unanswered_questions: list, chat_history: list = None, current_answers: dict = None) -> str:
        if not unanswered_questions:
            return "所有問題都已回答。謝謝！"
        
        sorted_unanswered = sorted(unanswered_questions, key=lambda x: (x.get("validation_rule") == "required", x.get("priority", 99)))
        
        questions_to_mention_candidates = []
        # 優先選擇那些在 current_answers 中還沒有任何有效答案的問題
        for q_obj in sorted_unanswered:
            if q_obj["id"] not in current_answers or current_answers.get(q_obj["id"]) is None:
                 questions_to_mention_candidates.append(q_obj)
        
        questions_to_mention = questions_to_mention_candidates[:2] if questions_to_mention_candidates else sorted_unanswered[:1]


        questions_list_text = ""
        if questions_to_mention:
            questions_list_text = "例如：「" + "」、「".join([q["question"] for q in questions_to_mention]) + "」。"
        else: # 理論上不應該到這裡，因為 unanswered_questions 不為空
            questions_list_text = "您可以繼續提供其他資訊。" 

        system_prompt = f"""
        你是一個友善的問卷AI助理。問卷尚未完成，還有一些問題需要使用者回答。
        請根據這些未回答的問題，生成一個自然、引導性強的提示語，鼓勵使用者繼續提供資訊。
        語氣要溫和，像是在聊天。不要列出所有問題，可以概括性地提問，或者挑選一兩個最重要的來提問。
        請參考對話歷史和目前已收集的答案來判斷接下來如何提問最自然，避免重複提問用戶剛剛或之前已經明確回答過或提及過的內容。
        同時，請在提示語中包含一句話，提醒使用者可以「隨時修改之前提供的答案」。

        目前尚未回答的問題包括：{', '.join([q['question'] for q in sorted_unanswered])}
        你可以嘗試引導他們回答其中一個或幾個，例如：{questions_list_text}
        """
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-4:])
        messages.append({"role": "user", "content": "請生成一個引導使用者繼續回答問題的提示語。"})
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"生成下一步提示時發生錯誤: {e}")
            return "我們還有一些問題需要您的協助。請問您是否願意繼續？您也可以隨時說出想修改的答案。"

    def generate_clarification_prompt(self, question_id: str, problem_description: str, chat_history: list = None) -> str:
        question_obj = next((q for q in self.question_structure if q["id"] == question_id), None)
        question_text = question_obj["question"] if question_obj else question_id
        system_prompt = f"""
        你是一個友善的問卷AI助理。我們在處理使用者最近的回答時遇到一些不明確的地方，需要澄清。
        請根據問題描述，生成一個禮貌、清晰的澄清提問語，引導使用者提供更準確的資訊。
        提及是關於哪個問題的。

        相關問題: {question_text}
        問題描述: {problem_description}
        請用中文回答。
        """
        messages = [{"role": "system", "content": system_prompt}]
        if chat_history:
            messages.extend(chat_history[-2:])
        messages.append({"role": "user", "content": "請生成澄清提示。"})
        try:
            response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=0.7)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"生成澄清提示時發生錯誤: {e}")
            return "您剛才的回答我有點不確定，可以請您再說清楚一點嗎？"