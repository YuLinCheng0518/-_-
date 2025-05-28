# 問卷 AI Agent

[![OpenAI](https://img.shields.io/badge/OpenAI-Realtime_API-412991?style=flat-square&logo=openai)](https://platform.openai.com/docs/guides/realtime-conversations)
[![n8n](https://img.shields.io/badge/n8n-Workflow_Automation-FF0000?style=flat-square&logo=n8n)](https://n8n.io/)
[![JavaScript](https://img.shields.io/badge/JavaScript-Client_Side-F7DF1E?style=flat-square&logo=javascript)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![Google Sheets](https://img.shields.io/badge/Google_Sheets-Data_Storage-34A853?style=flat-square&logo=googlesheets)](https://www.google.com/sheets/about/)

這是一個基於 Python 和 OpenAI API 實現的對話式問卷 AI Agent。它能夠透過自然語言與使用者互動，收集問卷答案並寫入 Google Sheet。

---

## ✨ 功能特性

- **自然語言交互**：使用者可透過對話形式回答問題，無需照格式。
- **智能答案提取**：使用 LLM 將自由文字轉為結構化欄位。
- **上下文記憶**：Agent 會記住對話歷史，讓問答更自然。
- **動態題目流程**：依使用者回答動態決定下一題。
- **答案修正澄清**：可針對模糊或錯誤的回答進行澄清。
- **跳題邏輯處理**：支援條件題目（例如低分才追問原因）。
- **Google Sheets 整合**：自動寫入問卷結果。
- **問卷定義靈活**：透過 `questionnaire_data.py` 自訂問卷架構。

---

## 🧰 技術棧

- **語言**：Python 3.x
- **核心模型**：OpenAI GPT 系列（如 `gpt-3.5-turbo`）
- **Google Sheets API**：使用 `gspread` 存取資料
- **驗證機制**：透過 `google-auth`, `google-auth-oauthlib`

---

## 📁 專案結構

```
.
├── ai_agent.py                # 對話流程與任務管理
├── ai_nlu_layer.py           # 與 OpenAI 溝通的自然語言處理模組
├── google_sheets_service.py  # 與 Google Sheets 溝通的模組
├── questionnaire_data.py     # 問卷定義與條件邏輯設定
├── main.py                   # 執行入口
├── service_account.json      # GCP 服務帳戶金鑰
└── README.md                 # 本說明文件
```

---

## 🚀 安裝與設定指南

### 1. 前置需求

- Python 3.7+
- 有效的 OpenAI API 金鑰
- Google Cloud Platform 帳戶

---

### 2. 設定 Google Sheets API

#### 步驟一：啟用 Sheets API

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇或建立專案
3. 點選「API 和服務」→「Library」
4. 搜尋「Google Sheets API」，點選啟用

#### 步驟二：建立服務帳戶

1. 進入「API 和服務」→「憑證」
2. 建立服務帳戶，完成後下載 JSON 金鑰
3. 將金鑰檔案命名為 `service_account.json` 放到專案根目錄

#### 步驟三：設定授權 Google Sheet

1. 建立 Google Sheet
2. 將服務帳戶 Email 加入為「編輯者」
3. 取得網址中的 Sheet ID，例如：  
   `https://docs.google.com/spreadsheets/d/**這裡是你的ID**/edit`

---

### 3. 安裝套件

```bash
pip install openai gspread google-auth google-auth-oauthlib
```

---

### 4. 設定環境變數

#### macOS / Linux

```bash
export OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

#### Windows CMD

```bash
set OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

#### PowerShell

```powershell
$env:OPENAI_API_KEY="sk-YourOpenAIKeyHere"
```

---

### 5. 編輯 `questionnaire_data.py`

修改以下欄位：

```python
GOOGLE_SHEET_ID = "你的 Google Sheet ID"
SERVICE_ACCOUNT_FILE = "service_account.json"

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

## ▶️ 啟動服務

```bash
python main.py
```

執行後，AI Agent 會開始與使用者互動並收集問卷資料。

---

## 📤 Google Sheets 輸出行為

- 程式啟動時會檢查並建立欄位
- 每次填寫完成後會新增一筆資料

---

## 💡 小技巧

- 可加入「條件題目」機制：如當使用者給低分才詢問為什麼。
- 可整合到 Line bot、Web Chatbot、App 中擴充應用場景。

---

## 📸 使用範例畫面

- ![問卷互動範例](問卷使用截圖.png)
- ![Google Sheet 結果](Google%20Sheet結果.png)
