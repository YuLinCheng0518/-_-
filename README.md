# 問卷 AI Agent

這是一個基於 Python 和 OpenAI API 實現的對話式問卷 AI Agent。它能夠透過自然語言與使用者進行互動，收集問卷答案，並將結果自動寫入 Google Sheet。

---

## ✨ 功能特性

- **自然語言交互**：使用者可用聊天方式回答問題，無需遵循固定格式。
- **智能答案提取**：使用大型語言模型 (LLM) 將回答轉換為結構化欄位。
- **上下文感知**：Agent 能夠記住對話歷史，使互動更自然連貫。
- **動態問題引導**：根據使用者已回答內容智能選擇下一題。
- **答案修改與澄清**：允許更正之前的答案，或處理模糊、不符合格式的回覆。
- **條件邏輯處理**：支援跳題邏輯（如當滿意度過低時才詢問原因）。
- **Google Sheets 整合**：自動將答案寫入指定的 Google Sheet。
- **靈活的問卷定義**：問卷結構可於 `questionnaire_data.py` 中輕鬆修改。

---

## 🧰 技術棧

- **程式語言**：Python 3.x
- **核心模型**：OpenAI API（如 `gpt-3.5-turbo` 或更高）
- **Google Sheets API**：`gspread` 函式庫
- **Google 認證**：`google-auth`, `google-auth-oauthlib`

---

## 📁 專案結構

```
.
├── ai_agent.py                # AI Agent 對話邏輯與流程管理
├── ai_nlu_layer.py           # 與 OpenAI API 的自然語言理解層
├── google_sheets_service.py  # Google Sheets 寫入與連線模組
├── questionnaire_data.py     # 問卷結構定義與設定
├── main.py                   # 主程式入口
├── service_account.json      # Google 服務帳戶金鑰 (使用者自行創建)
└── README.md                 # 本說明文件
```

---

## 🚀 安裝與設定指南

### 1. 前置需求

- Python 3.7+
- OpenAI API Key
- 一個 Google Cloud Platform (GCP) 帳戶

---

### 2. Google Cloud Platform 設定

#### 步驟一：啟用 Google Sheets API

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案，或選擇現有專案
3. 導航至 **APIs & Services → Library**
4. 搜尋「Google Sheets API」，點擊啟用

#### 步驟二：創建服務帳戶 (Service Account)

1. 前往 **APIs & Services → Credentials**
2. 點選 **CREATE CREDENTIALS → Service Account**
3. 填寫名稱與說明後點選 **DONE**

#### 步驟三：產生金鑰

1. 點選剛剛建立的服務帳戶 → 選擇 **KEYS** 分頁
2. 點選 **ADD KEY → Create new key**
3. 選擇 **JSON** 格式並下載檔案
4. 將檔案命名為 `service_account.json` 並放置於專案根目錄  
   ⚠️ **請勿將此檔提交至 GitHub**

#### 步驟四：建立 Google Sheet 並授權

1. 新建 Google Sheet
2. 將服務帳戶的 Email 加為「編輯者」
3. 記下 Google Sheet ID（來自網址中的 `/d/` 部分）

---

### 3. 安裝依賴套件

```bash
pip install openai gspread google-auth google-auth-oauthlib
```

---

### 4. 設定環境變數

設定 OpenAI API 金鑰：

**macOS / Linux**

```bash
export OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

**Windows CMD**

```bash
set OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

**PowerShell**

```powershell
$env:OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

---

### 5. 設定 `questionnaire_data.py`

打開並修改下列欄位：

- `GOOGLE_SHEET_ID`: 設為你的 Google Sheet ID
- `SERVICE_ACCOUNT_FILE`: 預設為 `"service_account.json"`
- `QUESTIONNAIRE_STRUCTURE`: 定義你的問卷，例如：

```python
QUESTIONNAIRE_STRUCTURE = [
    {
        "id": "email",
        "question": "請問你的電子信箱是？",
        "type": "text",
        "validation_rule": "required,email",
        "priority": 1,
        "mapping_context": "從回答中找出 email"
    },
    {
        "id": "satisfaction",
        "question": "你對我們的服務滿意嗎？（1~5 分）",
        "type": "number",
        "validation_rule": "range_1_5",
        "priority": 2
    },
    ...
]
```

---

## ▶️ 執行程式

```bash
python main.py
```

AI Agent 將啟動並開始對話收集問卷資料。

---

## 📤 Google Sheets 輸出

- 程式會在 Google Sheet 中自動建立欄位（若為空）。
- 每次問卷填寫完成後，自動新增一列填寫結果。

---

## 💡 小技巧

- 可加入條件問題，例如當使用者滿意度低於 3 分時才詢問具體原因。
- 可整合至 Line bot、Web chatbot 或應用程式中。

---

## 互動畫面）

- ![問卷互動範例](問卷使用截圖.png)
- ![問卷互動範例](Google%20Sheet結果.png)
