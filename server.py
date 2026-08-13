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
        "GetLoginData",
        LoginReq,
        {"account_id": account_id},
        # ЗАМЕНИТЬ на реальный тип ответа (скорее всего не LoginReq)
        MajorLoginRes,  # <-- поставь правильный тип из proto
        token,
    )
    print(f"\nGetLoginData status={ld['status']} len={ld['rawLen']} err={ld['err']}")
    print("  ->", json.dumps(pick(ld["decoded"], ["account_id", "nickname", "level", "exp", "coins", "gems", "region", "clan_id", "create_at"])))

    # 3) GetProfiles (authed)
    gp = call(
        "GetProfiles",
        AvatarProfile,
        {},
        CSGetProfileListRes,
        token,
    )
    profs = gp["decoded"].get("profiles", []) if gp["decoded"] else []
    selected = [p["avatar_id"] for p in profs if p.get("is_selected")]
    print(f"\nGetProfiles  status={gp['status']} len={gp['rawLen']} err={gp['err']}")
    print(f"  -> profiles={len(profs)} selected={json.dumps(selected)}")

    # 4) GetWallet (authed)
    gw = call(
        "GetWallet",
        CSGetWalletReq,
        {},
        CSGetWalletRes,
        token,
    )
    print(f"\nGetWallet    status={gw['status']} len={gw['rawLen']} err={gw['err']}")
    print("  ->", json.dumps(pick(gw["decoded"], ["account_id", "wallet"])))

    # 5) GetBackpack (authed)
    gb = call(
        "GetBackpack",
        CSGetBackpackReq,
        {"is_login": True},
        CSGetBackpackRes,
        token,
    )
    items = gb["decoded"].get("items", []) if gb["decoded"] else []
    sel = (gb["decoded"] or {}).get("selected_items") or {}
    selected_avatar = sel.get("avatar_id")
    print(f"\nGetBackpack  status={gb['status']} len={gb['rawLen']} err={gb['err']}")
    print(f"  -> wallet={json.dumps(gb['decoded'].get('wallet'))} items={len(items)} selected_avatar={selected_avatar}")

    # 6) GetMailList (authed)
    gm = call(
        "GetMailList",
        CSGetMailListReq,
        {"language": "en"},
        CSGetMailListRes,
        token,
    )
    mails = gm["decoded"].get("mails", []) if gm["decoded"] else []
    print(f"\nGetMailList  status={gm['status']} len={gm['rawLen']} err={gm['err']}")
    print(f"  -> mails={len(mails)}")

    print("\n=== DONE ===")
    print(f"TOKEN={token}")
    print(f"ACCOUNT_ID={account_id}")

if __name__ == "__main__":
    main()
