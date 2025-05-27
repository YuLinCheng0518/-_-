QUESTIONNAIRE_STRUCTURE = [
    {
        "id": "name",
        "question": "您好！請問您的姓名是？",
        "type": "text",
        "validation_rule": "required",
        "context": "詢問使用者的全名，例如：王小明",
        "mapping_context": "提取使用者的姓名或全名。",
        "priority": 1 # 問題優先級，用於排序提問
    },
    {
        "id": "email",
        "question": "您的電子郵件地址是？ (用於寄送問卷結果或後續通知)",
        "type": "text",
        "validation_rule": "email", # 這裡仍使用email驗證，但由於LLM的判斷會更智能
        "context": "詢問使用者的電子郵件地址，例如：test@example.com",
        "mapping_context": "提取有效的電子郵件地址。",
        "priority": 2
    },
    {
        "id": "age_group",
        "question": "請問您的年齡區間是？",
        "type": "select",
        "options": ["18-24", "25-34", "35-44", "45-54", "55+"],
        "validation_rule": "required",
        "context": "讓使用者從提供的年齡區間選項中選擇，例如：25-34",
        "mapping_context": "將使用者的年齡描述映射到 ['18-24', '25-34', '35-44', '45-54', '55+'] 中的一個選項。",
        "priority": 3
    },
    {
        "id": "product_satisfaction",
        "question": "您對我們產品的整體滿意度如何？ (1-非常不滿意，5-非常滿意)",
        "type": "number",
        "validation_rule": "range_1_5",
        "context": "詢問產品滿意度，需是1到5的數字，例如：4",
        "mapping_context": "提取使用者對產品的滿意度，數字範圍是1到5。",
        "priority": 4 
    },
    {
        "id": "detailed_dissatisfaction_reason", # 條件必填問題
        "question": "很抱歉您對產品不滿意，請問具體原因是什麼？我們希望能改進。",
        "type": "text",
        "validation_rule": "required_if_triggered", # 修改為條件必填
        "context": "詢問使用者對產品不滿意的具體原因。",
        "mapping_context": "提取使用者對產品不滿意的具體原因或建議。",
        "priority": 5 
    },
    {
        "id": "feedback_comments",
        "question": "您對我們的產品有任何其他建議或意見嗎？ (可選)",
        "type": "text",
        "context": "使用者對產品的開放式意見或建議，例如：希望加入更多功能",
        "mapping_context": "提取使用者對產品的任何其他意見或建議。",
        "priority": 6
    },
    {
        "id": "allow_follow_up",
        "question": "您是否同意我們在未來進行後續追蹤或發送相關資訊？ (是/否)",
        "type": "boolean",
        "validation_rule": "yes_no",
        "context": "確認使用者是否同意後續追蹤，回答 '是' 或 '否'",
        "mapping_context": "判斷使用者是否同意後續追蹤，結果應為 '是' 或 '否'。",
        "priority": 7
    }
]


# Google Sheet 的列標題，必須與 QUESTIONNAIRE_STRUCTURE 中的 'id' 保持一致且順序正確
GOOGLE_SHEET_HEADERS = [q["id"] for q in QUESTIONNAIRE_STRUCTURE]

# Google Sheet 配置
GOOGLE_SHEET_ID = "1dloIdYeMpwW7Mqg6LF63MYMbNrl7YSJxFwcYQYB9ryo" # 請替換為你的 Google Sheet ID
SERVICE_ACCOUNT_FILE = "your_path_to_service_account.json" # 你的服務帳戶金鑰檔案路徑
