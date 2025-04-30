# lambda/index.py
import json
import os
import re  # 正規表現モジュールをインポート
from urllib import request , error

#Fast API：endpoint
API_URL = "https://abcdefgh.ngrok.io/generate"

# Lambda ハンドラー関数
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        # 会話履歴にユーザーメッセージを追加
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })

        request_payload = {
            "prompt": message,
            "max_new_tokens": 512,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }

        # JSON → バイト列に変換
        data = json.dumps(request_payload).encode("utf-8")

        # 3. FastAPI サーバーへ POST リクエスト
        req = request.Request(
            API_URL,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with request.urlopen(req) as resp:
            resp_text = resp.read().decode("utf-8")
            status_code = resp.getcode()

        if status_code != 200:
            raise Exception(f"FastAPI サーバーからエラー: {status_code}")

        resp_json = json.loads(resp_text)
        assistant_response = resp_json.get("generated_text")
        if not assistant_response:
            raise Exception("FastAPI の応答に generated_text がありません")

        # 会話履歴にアシスタントの応答を追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

    except error.HTTPError as e:
        # FastAPI 側の エラー
        err_body = e.read().decode("utf-8")
        print(f"HTTPError: {e.code} {e.reason} {err_body}")
        return {
            "statusCode": 502,
            "body": json.dumps({"success": False, "error": f"FastAPI エラー {e.code}: {err_body}"})
        }
    except error.URLError as e:
        # ネットワークエラー
        print(f"URLError: {e.reason}")
        return {
            "statusCode": 502,
            "body": json.dumps({"success": False, "error": f"接続エラー: {e.reason}"})
        }
    except Exception as error:
        # その他
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "body": json.dumps({"success": False, "error": str(error)})
        }
