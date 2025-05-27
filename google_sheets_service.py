# google_sheets_service.py

import gspread
from google.oauth2.service_account import Credentials
import os

def get_google_sheet_client(service_account_file):
    """
    獲取 Google Sheets API 客戶端。
    """
    # 定義認證範圍
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    # 從服務帳戶文件加載憑證
    try:
        creds = Credentials.from_service_account_file(service_account_file, scopes=scope)
        client = gspread.authorize(creds)
        print(f"成功連接 Google Sheets API 客戶端.")
        return client
    except Exception as e:
        print(f"連接 Google Sheets API 失敗: {e}")
        print(f"請確保服務帳戶文件 '{service_account_file}' 存在且有效，並且已在 GCP 中啟用相關 API。")
        return None

def append_row_to_sheet(client, sheet_id, worksheet_name, data_row, headers):
    """
    將數據行寫入 Google Sheet。
    """
    try:
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet(worksheet_name)

        # 檢查工作表是否為空，如果是，則寫入標題行
        if not worksheet.get_all_values():
            worksheet.append_row(headers)
            print(f"已在 '{worksheet_name}' 工作表寫入標題行。")

        worksheet.append_row(data_row)
        print(f"數據已成功寫入 Google Sheet '{worksheet_name}'。")
        return True
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"錯誤：Google Sheet ID '{sheet_id}' 未找到。請檢查 ID 是否正確。")
        return False
    except gspread.exceptions.WorksheetNotFound:
        print(f"錯誤：工作表 '{worksheet_name}' 未找到。請檢查工作表名稱是否正確。")
        return False
    except Exception as e:
        print(f"將數據寫入 Google Sheet 時發生錯誤: {e}")
        print(f"請確保服務帳戶已具有該 Google Sheet 的編輯權限。")
        return False

if __name__ == '__main__':
    # 這是一個簡單的測試用例
    from questionnaire_data import GOOGLE_SHEET_ID, SERVICE_ACCOUNT_FILE, GOOGLE_SHEET_HEADERS

    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"錯誤：服務帳戶文件 '{SERVICE_ACCOUNT_FILE}' 不存在。無法執行測試。")
    else:
        gs_client = get_google_sheet_client(SERVICE_ACCOUNT_FILE)
        if gs_client:
            test_data = ["測試名稱", "test@example.com", "25-34", "4", "這是一個測試意見。", "是"]
            append_row_to_sheet(gs_client, GOOGLE_SHEET_ID, "工作表1", test_data, GOOGLE_SHEET_HEADERS)