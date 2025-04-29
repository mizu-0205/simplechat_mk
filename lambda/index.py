# lambda/index.py
import json
import os
import boto3
import re  # 正規表現モジュールをインポート
from botocore.exceptions import ClientError
import urllib.request
import urllib.error

#FAstAPIのURLを環境変数から取得
FASTAPI_URL      = os.environ.get("https://478e-35-198-202-33.ngrok-free.app")   
FASTAPI_ENDPOINT = f"{FASTAPI_URL.rstrip('/')}/generate" if FASTAPI_URL else None

#lamda endpoint作成
def lambda_handler(event, context):
    try:
        if FASTAPI_ENDPOINT is None:
            raise RuntimeError("環境変数 FASTAPI_URL が設定されていません")

        # リクエストボディの解析
        body = json.loads(event.get("body", "{}"))
        message = body["message"]
        conversation_history = body.get("conversationHistory", [])

        # FastAPI へ転送
        payload = json.dumps({
            "message": message,
            "conversationHistory": conversation_history
        }).encode("utf-8")

        req = urllib.request.Request(
            FASTAPI_ENDPOINT,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            fastapi_resp = json.loads(resp.read().decode("utf-8"))

        if not fastapi_resp.get("success"):
            raise RuntimeError(fastapi_resp.get("error", "Unknown FastAPI error"))

        assistant_response  = fastapi_resp["response"]
        conversation_history = fastapi_resp.get("conversationHistory", conversation_history)

        # 成功レスポンス
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": conversation_history
            })
        }

    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        error_msg = f"FastAPI HTTPError {e.code}: {detail}"
    except Exception as e:
        error_msg = str(e)

    # エラー時レスポンス
    return {
        "statusCode": 500,
        "body": json.dumps({
            "success": False,
            "error": error_msg
        })
    }