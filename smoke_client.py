import json
import requests
from google.protobuf.message import Message

# Подключи свои proto-классы. Имена должны совпадать с теми, что сгенерированы protoc.
# Пример (заглушки, замени на реальные импорты):
# from login_pb2 import LoginReq, MajorLoginRes
# from profile_pb2 import AvatarProfile, CSGetProfileListRes
# from wallet_pb2 import CSGetWalletReq, CSGetWalletRes
# from backpack_pb2 import CSGetBackpackReq, CSGetBackpackRes
# from mail_pb2 import CSGetMailListReq, CSGetMailListRes

# ------------------------------------------------------------------
# ВСТАВЬ РЕАЛЬНЫЕ ИМПОРТЫ НИЖЕ
# ------------------------------------------------------------------
from my_protos import (
    LoginReq, MajorLoginRes,
    AvatarProfile, CSGetProfileListRes,
    CSGetWalletReq, CSGetWalletRes,
    CSGetBackpackReq, CSGetBackpackRes,
    CSGetMailListReq, CSGetMailListRes,
)
# ------------------------------------------------------------------

from aes_helper import encrypt_aes

HOST = "127.0.0.1"  # локально; в Docker-сети — имя сервиса
PORT = 3000
BASE_URL = f"http://{HOST}:{PORT}"

def pick(obj, keys):
    if not obj:
        return {}
    return {k: obj[k] for k in keys if k in obj}

def call(endpoint, req_type, req_obj, res_type, token=None):
    # Protobuf: сериализуем в байты
    msg = req_type(**req_obj) if req_obj else req_type()
    plain = msg.SerializeToString()

    # AES: шифруем
    cipher = encrypt_aes(plain)

    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(cipher)),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.post(f"{BASE_URL}/{endpoint}", data=cipher, headers=headers, timeout=10)
    body = resp.content

    decoded = None
    err = None
    try:
        res_msg = res_type()
        res_msg.ParseFromString(body)
        # Превращаем protobuf в dict для удобного вывода
        decoded = {f.name: getattr(res_msg, f.name) for f in res_msg.DESCRIPTOR.fields}
    except Exception as e:
        err = str(e)

    return {"status": resp.status_code, "decoded": decoded, "err": err, "rawLen": len(body)}

def main():
    print("=== BOOT SEQUENCE ===\n")

    # 1) MajorLogin (public)
    login = call(
        "MajorLogin",
        LoginReq,
        {
            "open_id": "boot-test-002",
            "open_id_type": 1,
            "nickname": "BootTester",
            "device_id": "dev-boot-001",
            "client_version": "1.70.4",
        },
        MajorLoginRes,
        None,
    )
    print(f"MajorLogin   status={login['status']} len={login['rawLen']} err={login['err']}")
    print("  ->", json.dumps(pick(login["decoded"], ["account_id", "token", "ttl", "server_url", "ip_region", "recommend_regions"])))

    token = login["decoded"].get("token") if login["decoded"] else None
    if not token:
        print("NO TOKEN - aborting")
        return

    account_id = login["decoded"]["account_id"]

    # 2) GetLoginData (authed) — проверь, какой тип ответа реально ожидает сервер
    ld = call(
