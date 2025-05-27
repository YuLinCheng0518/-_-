# ai_agent.py

import re
import os
from questionnaire_data import QUESTIONNAIRE_STRUCTURE, GOOGLE_SHEET_HEADERS, GOOGLE_SHEET_ID, SERVICE_ACCOUNT_FILE
from google_sheets_service import get_google_sheet_client, append_row_to_sheet
from ai_nlu_layer import AINLULayer
import time # 用於模擬思考時間

class QuestionnaireAgent:
    def __init__(self):
        self.question_structure = QUESTIONNAIRE_STRUCTURE
        self.collected_answers = {q["id"]: None for q in QUESTIONNAIRE_STRUCTURE}
        
        self.unanswered_questions_ids = set(q["id"] for q in QUESTIONNAIRE_STRUCTURE)
        self.unanswered_questions_ids.discard("detailed_dissatisfaction_reason") 

        self.gs_client = None
        self.nlu_agent = None
        self.chat_history = []
        self.total_questions_count = len(QUESTIONNAIRE_STRUCTURE)

    def _initialize_gs_client(self):
        if not self.gs_client:
            if not os.path.exists(SERVICE_ACCOUNT_FILE):
                print(f"錯誤：服務帳戶文件 '{SERVICE_ACCOUNT_FILE}' 不存在。無法連接 Google Sheets。")
                return None
            self.gs_client = get_google_sheet_client(SERVICE_ACCOUNT_FILE)
        return self.gs_client
    
    def _initialize_nlu_agent(self):
        if not self.nlu_agent:
            try:
                self.nlu_agent = AINLULayer()
                print("NLU Agent 已初始化成功。")
            except ValueError as e:
                print(f"NLU Agent 初始化失敗: {e}")
                print("請確保已設定 OPENAI_API_KEY 環境變數或在 AINLULayer 構造函數中傳入。")
                self.nlu_agent = None
        return self.nlu_agent

    def _get_question_obj_by_id(self, q_id):
        for q in self.question_structure:
            if q["id"] == q_id:
                return q
        return None

    def _validate_extracted_answer(self, question_obj, extracted_answer):
        q_id = question_obj["id"]
        q_type = question_obj.get("type")
        validation_rule = question_obj.get("validation_rule")
        options = question_obj.get("options", [])

        is_required = False
        if validation_rule == "required":
            is_required = True
        elif validation_rule == "required_if_triggered" and q_id == "detailed_dissatisfaction_reason":
            product_satisfaction = self.collected_answers.get("product_satisfaction")
            if product_satisfaction is not None and product_satisfaction in [1, 2]:
                is_required = True
            if not is_required:
                return True, None, None 

        # 如果提取的答案是 None 或空字串
        if extracted_answer is None or (isinstance(extracted_answer, str) and not extracted_answer.strip()):
            if is_required:
                return False, None, "這個問題是必填的，但我們未能從您的回答中提取到有效資訊。"
            else: # 非必填，且答案為空，視為有效，但答案為 None
                return True, None, None 

        # 類型和規則驗證 (對於非空答案)
        if q_type == "number":
            try:
                num_input = int(extracted_answer)
                if validation_rule == "range_1_5" and not (1 <= num_input <= 5):
                    return False, None, "您提供的數字不在有效範圍 (1-5) 內。"
                return True, num_input, None 
            except ValueError:
                return False, None, "無法將您的回答轉換為有效的數字。請確保您的回答包含數字。"
        elif q_type == "select":
            matched_option = None
            for opt in options:
                if isinstance(extracted_answer, str) and extracted_answer.lower() == opt.lower():
                    matched_option = opt
                    break
            if matched_option:
                return True, matched_option, None
            else:
                # 嘗試更寬鬆的匹配：如果 extracted_answer 只是數字，且選項也是數字
                if isinstance(extracted_answer, (int, str)) and str(extracted_answer).isdigit():
                    for opt in options: # e.g. age_group 37 -> "35-44"
                        if '-' in opt:
                            try:
                                low, high = map(int, opt.split('-'))
                                if low <= int(extracted_answer) <= high:
                                    return True, opt, None
                            except ValueError:
                                pass
                return False, None, f"您選擇的選項不在有效列表中。請從以下選項中選擇一個：{', '.join(options)}。"
        elif q_type == "boolean":
            if isinstance(extracted_answer, str):
                if extracted_answer.lower() in ["是", "yes"]:
                    return True, "是", None
                elif extracted_answer.lower() in ["否", "no"]:
                    return True, "否", None
            return False, None, "無法將您的回答解析為 '是' 或 '否'。請嘗試更直接的回答。"
        elif q_type == "text":
            if validation_rule == "email":
                if not re.match(r"[^@]+@[^@]+\.[^@]+", str(extracted_answer)):
                    return False, None, "您提供的電子郵件格式無效。請輸入一個有效的電子郵件地址。"
        
        return True, extracted_answer, None

    def _update_answers_and_unanswered_status(self, q_id, validated_answer):
        is_actually_updated = False 
        old_answer = self.collected_answers.get(q_id)

        # 只有當有實際的、非 None 的答案被提供，並且與舊答案不同時，才算「更新」
        if validated_answer is not None and old_answer != validated_answer:
            self.collected_answers[q_id] = validated_answer
            is_actually_updated = True
            
            if q_id in self.unanswered_questions_ids: # 如果之前是未回答
                self.unanswered_questions_ids.discard(q_id)
                print(f"✅ 已成功獲取 '{self._get_question_obj_by_id(q_id)['question']}' 的答案。")
            else: # 更新已回答的答案
                print(f"🔄 已更新 '{self._get_question_obj_by_id(q_id)['question']}' 的答案。")
        elif validated_answer is None and old_answer is not None and q_id not in self.unanswered_questions_ids:
            # 如果之前有答案，現在變成 None (例如被修改為空，或因條件變化而不再需要)
            # 但問題本身並非「未回答」狀態（除非它是必填）
            # 這種情況通常是LLM提取為null，然後驗證也認為null是可接受的（非必填）
            # 除非是使用者明確修改為空，否則不應該輕易將已回答問題標為未回答
            # self.collected_answers[q_id] = None # 確保記錄為 None
            # is_actually_updated = True
            pass # 保持原樣，如果 validated_answer 是 None，不應觸發 "已成功獲取"


        # 處理 'product_satisfaction' 的條件邏輯
        if q_id == "product_satisfaction":
            detailed_reason_q_id = "detailed_dissatisfaction_reason"
            detailed_reason_q_obj = self._get_question_obj_by_id(detailed_reason_q_id)
            
            current_ps_answer = self.collected_answers.get("product_satisfaction") # 以最新的為準

            if current_ps_answer is not None and current_ps_answer in [1, 2]:
                if detailed_reason_q_id not in self.unanswered_questions_ids and self.collected_answers.get(detailed_reason_q_id) is None:
                    self.unanswered_questions_ids.add(detailed_reason_q_id) 
                    print(f"👉 您的產品滿意度較低，問題 '{detailed_reason_q_obj['question']}' 現為必填。")
            else: 
                if detailed_reason_q_id in self.unanswered_questions_ids:
                    self.unanswered_questions_ids.discard(detailed_reason_q_id) 
                    if self.collected_answers.get(detailed_reason_q_id) is not None: # 只有當之前有答案才提示跳過
                        print(f"👉 您的產品滿意度良好，問題 '{detailed_reason_q_obj['question']}' 已被跳過。")
                if self.collected_answers.get(detailed_reason_q_id) is not None:
                    self.collected_answers[detailed_reason_q_id] = None
                    # print(f"👉 先前提供的關於不滿意原因的回答已被清除。") # 這個提示可能太頻繁
        
        return is_actually_updated

    def start_questionnaire(self):
        print("--- 正在啟動智能問卷助手... ---")
        if not self._initialize_nlu_agent():
            print("初始化失敗，問卷無法啟動。")
            return

        initial_greeting = self.nlu_agent.generate_initial_greeting_and_guidance()
        print(f"\nAI: {initial_greeting}")
        self.chat_history.append({"role": "assistant", "content": initial_greeting})
        print("-" * 30)

        user_raw_input = input("您: ")
        self.chat_history.append({"role": "user", "content": user_raw_input})

        while True: 
            # 檢查是否為明確的結束指令
            if user_raw_input.lower() in ["結束問卷", "完成問卷", "結束", "完成", "我想結束", "不用了", "quit", "exit", "done"]:
                # 在真正結束前，檢查是否有必填問題未完成
                pending_required = [
                    q_id for q_id in self.unanswered_questions_ids 
                    if self._get_question_obj_by_id(q_id).get("validation_rule") == "required" or 
                       (self._get_question_obj_by_id(q_id).get("validation_rule") == "required_if_triggered" and 
                        self.collected_answers.get("product_satisfaction") in [1,2] and 
                        self.collected_answers.get(q_id) is None)
                ]
                if pending_required:
                    confirm_exit = input(f"AI: 您還有 {len(pending_required)} 個重要問題尚未回答，確定要現在結束嗎？ (是/否) ")
                    self.chat_history.append({"role": "assistant", "content": f"您還有 {len(pending_required)} 個重要問題尚未回答，確定要現在結束嗎？"})
                    self.chat_history.append({"role": "user", "content": confirm_exit})
                    if confirm_exit.lower() not in ["是", "yes"]:
                        print("AI: 好的，我們繼續。")
                        # 需要重新生成提問
                        current_unanswered_questions_objs = [self._get_question_obj_by_id(q_id) for q_id in self.unanswered_questions_ids if self._get_question_obj_by_id(q_id) is not None]
                        next_prompt = self.nlu_agent.generate_next_questions_prompt(current_unanswered_questions_objs, self.chat_history, self.collected_answers)
                        print(f"\nAI: {next_prompt}")
                        self.chat_history.append({"role": "assistant", "content": next_prompt})
                        user_raw_input = input("您: ")
                        self.chat_history.append({"role": "user", "content": user_raw_input})
                        continue 
                print("AI: 好的，感謝您的參與。問卷已結束。")
                break

            print("AI: 正在分析您的回答... (請稍候)")
            time.sleep(0.5) # 減少等待時間

            nlu_result = self.nlu_agent.parse_chat_response_to_answers(
                user_raw_input, 
                self.question_structure, 
                self.collected_answers, 
                self.chat_history
            )

            action_request = nlu_result.get("action_request")
            extracted_answers_map = nlu_result.get("extracted_answers", {})
            reasoning = nlu_result.get("reasoning", "")

            if action_request == "error":
                error_msg = f"抱歉，我在處理您的回答時遇到問題: {reasoning} 請您再試一次。"
                print(f"AI: {error_msg}")
                self.chat_history.append({"role": "assistant", "content": error_msg})
                user_raw_input = input("您: ")
                self.chat_history.append({"role": "user", "content": user_raw_input})
                continue 
            
            if action_request == "finish_questionnaire": 
                # 這裡的邏輯與上面的結束指令檢查重複了，可以合併
                # 暫時先保留，確保 LLM 的結束意圖也被處理
                # 在真正結束前，檢查是否有必填問題未完成
                pending_required = [
                    q_id for q_id in self.unanswered_questions_ids 
                    if self._get_question_obj_by_id(q_id).get("validation_rule") == "required" or 
                       (self._get_question_obj_by_id(q_id).get("validation_rule") == "required_if_triggered" and 
                        self.collected_answers.get("product_satisfaction") in [1,2] and 
                        self.collected_answers.get(q_id) is None)
                ]
                if pending_required:
                    confirm_exit = input(f"AI: 您還有 {len(pending_required)} 個重要問題尚未回答，確定要現在結束嗎？ (是/否) ")
                    self.chat_history.append({"role": "assistant", "content": f"您還有 {len(pending_required)} 個重要問題尚未回答，確定要現在結束嗎？"})
                    self.chat_history.append({"role": "user", "content": confirm_exit})
                    if confirm_exit.lower() not in ["是", "yes"]:
                        print("AI: 好的，我們繼續。")
                        current_unanswered_questions_objs = [self._get_question_obj_by_id(q_id) for q_id in self.unanswered_questions_ids if self._get_question_obj_by_id(q_id) is not None]
                        next_prompt = self.nlu_agent.generate_next_questions_prompt(current_unanswered_questions_objs, self.chat_history, self.collected_answers)
                        print(f"\nAI: {next_prompt}")
                        self.chat_history.append({"role": "assistant", "content": next_prompt})
                        user_raw_input = input("您: ")
                        self.chat_history.append({"role": "user", "content": user_raw_input})
                        continue
                print("AI: 好的，您已選擇結束問卷。")
                break 

            newly_updated_count = 0
            validation_failures = [] 

            if extracted_answers_map: # 只有當LLM提取到東西時才處理
                for q_id, llm_extracted_value in extracted_answers_map.items():
                    question_obj = self._get_question_obj_by_id(q_id)
                    if not question_obj:
                        continue
                    is_valid, validated_value, error_msg = self._validate_extracted_answer(question_obj, llm_extracted_value)
                    if is_valid:
                        if self._update_answers_and_unanswered_status(q_id, validated_value):
                            newly_updated_count += 1
                    else:
                        if llm_extracted_value is not None and (isinstance(llm_extracted_value, str) and llm_extracted_value.strip()):
                            validation_failures.append({
                                "question_id": q_id,
                                "question_text": question_obj["question"],
                                "user_input_segment": llm_extracted_value,
                                "reason": error_msg
                            })
            
            if validation_failures:
                for failure in validation_failures:
                    clarification_prompt = self.nlu_agent.generate_clarification_prompt(
                        failure['question_id'],
                        f"關於「{failure['question_text']}」，您說了「{failure['user_input_segment']}」，但它{failure['reason']}。可以請您再說清楚一點嗎？",
                        self.chat_history
                    )
                    print(f"\nAI: {clarification_prompt}")
                    self.chat_history.append({"role": "assistant", "content": clarification_prompt})
            elif len(self.unanswered_questions_ids) == 0:
                print("\nAI: 感謝您的配合！所有問題都已完成。您可以說「結束」來提交問卷。")
                self.chat_history.append({"role": "assistant", "content": "所有問題都已完成。"})
            elif newly_updated_count == 0 and action_request == "no_change" and not extracted_answers_map:
                # 只有當LLM明確說no_change且沒有提取到任何答案時，才提示這個
                no_change_msg = "AI: 您的回答似乎沒有提供新的問卷資訊，或者我還未能完全理解。如果您想修改答案，請直接說明要修改哪個問題。"
                print(no_change_msg)
                self.chat_history.append({"role": "assistant", "content": no_change_msg})
            else: 
                current_unanswered_questions_objs = [self._get_question_obj_by_id(q_id) for q_id in self.unanswered_questions_ids if self._get_question_obj_by_id(q_id) is not None]
                if not current_unanswered_questions_objs and len(self.unanswered_questions_ids) > 0:
                     # 這種情況可能是 unanswered_questions_ids 中有ID，但 get_question_obj_by_id 返回None
                     # 理論上不應發生，但作為防禦
                    print(f"警告: unanswered_questions_ids 中包含無效ID: {self.unanswered_questions_ids}")
                    print("\nAI: 感謝您的配合！所有問題都已完成。您可以說「結束」來提交問卷。")
                elif current_unanswered_questions_objs:
                    next_prompt = self.nlu_agent.generate_next_questions_prompt(current_unanswered_questions_objs, self.chat_history, self.collected_answers)
                    print(f"\nAI: {next_prompt}")
                    self.chat_history.append({"role": "assistant", "content": next_prompt})
                else: # 所有問題都回答完了
                     print("\nAI: 感謝您的配合！所有問題都已完成。您可以說「結束」來提交問卷。")


            # 更新計數顯示
            actually_answered_count = 0
            for q_id_check in self.question_structure:
                if self.collected_answers.get(q_id_check["id"]) is not None: # 只要答案不是None就算回答了
                    # 對於 detailed_dissatisfaction_reason，如果它不該被問，即使答案是None也不算未回答
                    if q_id_check["id"] == "detailed_dissatisfaction_reason":
                        product_satisfaction = self.collected_answers.get("product_satisfaction")
                        if product_satisfaction is not None and product_satisfaction not in [1, 2]:
                            # 這種情況下，detailed_dissatisfaction_reason 不應被計算為未回答
                            pass # 不增加 actually_answered_count，也不將其視為未回答
                        elif self.collected_answers.get(q_id_check["id"]) is not None:
                             actually_answered_count +=1
                    else:
                        actually_answered_count +=1
            
            # 計算真正未回答的問題數量
            true_unanswered_count = self.total_questions_count - actually_answered_count
            # 確保 detailed_dissatisfaction_reason 在不需要時不被計入未回答
            if self.collected_answers.get("product_satisfaction") is not None and \
               self.collected_answers.get("product_satisfaction") not in [1, 2] and \
               "detailed_dissatisfaction_reason" in self.unanswered_questions_ids:
                # 如果產品滿意度高，但 detailed_dissatisfaction_reason 仍在未回答列表，則不應計入
                # （這通常在 _update_answers_and_unanswered_status 中處理，但這裡再確認）
                pass


            print(f"目前已收集到 {actually_answered_count} / {self.total_questions_count} 個問題的有效答案。")
            print("-" * 30) 
            
            user_raw_input = input("您: ")
            self.chat_history.append({"role": "user", "content": user_raw_input})

        print("\n--- 問卷已完成或提前結束 ---")
        print("我們正在將您的回答儲存到資料庫中...")
        self._save_answers_to_sheet()
        print("問卷結束。")

    def _save_answers_to_sheet(self):
        if not self._initialize_gs_client():
            print("無法連接 Google Sheets，答案未能儲存。")
            return
        data_row = []
        for header_id in GOOGLE_SHEET_HEADERS:
            val = self.collected_answers.get(header_id)
            data_row.append(val if val is not None else "")
        success = append_row_to_sheet(self.gs_client, GOOGLE_SHEET_ID, "工作表1", data_row, GOOGLE_SHEET_HEADERS)
        if success:
            print("您的問卷答案已成功儲存！")
        else:
            print("儲存問卷答案到 Google Sheet 時發生錯誤。請稍後再試或聯繫管理員。")