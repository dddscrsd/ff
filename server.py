import asyncio
import json
from typing import Any, Dict, Optional, List

import aiohttp
from google.protobuf.message import Message
# Импортируй свои сгенерированные proto-классы.
# Пример: from my_protos import LoginReq, MajorLoginRes, AvatarProfile, ...
# Ниже — заглушки, чтобы код был валидным; замени на реальные импорты.
from my_protos import (
    LoginReq, MajorLoginRes,
    AvatarProfile, CSGetProfileListRes,
    CSGetWalletReq, CSGetWalletRes,
    CSGetBackpackReq, CSGetBackpackRes,
    CSGetMailListReq, CSGetMailListRes,
)

# ------------------------------------------------------------------
# ВАЖНО: Подключи РЕАЛЬНЫЙ AES, идентичный Node-версии
# ------------------------------------------------------------------
def encrypt_aes(data: bytes) -> bytes:
    # Здесь должен быть тот же AES (режим, ключ, IV, padding), что и в Node
    raise NotImplementedError("Implement the exact same AES encryption as in Node.js")

def decrypt_aes(data: bytes) -> bytes:
    # Если сервер возвращает зашифрованные ответы — раскомментируй и реализуй
    # Иначе оставь как есть (сервер отдаёт plain protobuf)
    return data

# ------------------------------------------------------------------

HOST = "127.0.0.1"
PORT = 3000
BASE_URL = f"http://{HOST}:{PORT}"


def pick(obj: Optional[Dict[str, Any]], keys: List[str]) -> Dict[str, Any]:
    if not obj:
        return {}
    return {k: obj[k] for k in keys if k in obj}


async def post_cipher(
    session: aiohttp.ClientSession,
    endpoint: str,
    cipher: bytes,
    token: Optional[str] = None,
):
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(cipher)),
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    url = f"{BASE_URL}/{endpoint}"
    async with session.post(url, data=cipher, headers=headers) as resp:
        body = await resp.read()
        return resp.status, body


async def call(
    session: aiohttp.ClientSession,
    endpoint: str,
    req_type: type,
    req_obj: Dict[str, Any],
    res_type: type,
    token: Optional[str] = None,
):
    # Кодирование protobuf
    msg = req_type(**req_obj) if req_obj else req_type()
    plain = msg.SerializeToString()

    # Шифрование запроса
    cipher = encrypt_aes(plain)

    status, body = await post_cipher(session, endpoint, cipher, token)

    decoded = None
    err = None
    try:
        # Сервер возвращает plain protobuf (без шифрования)
        res_msg = res_type()
        res_msg.ParseFromString(body)
        decoded = {k: getattr(res_msg, k) for k in res_msg.DESCRIPTOR.fields_by_name.keys()}
    except Exception as e:
        err = str(e)

    return {"status": status, "decoded": decoded, "err": err, "rawLen": len(body)}


async def main():
    print("=== BOOT SEQUENCE ===\n")

    async with aiohttp.ClientSession() as session:
        # 1) MajorLogin (public)
        login = await call(
            session,
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

        # 2) GetLoginData (authed)
        ld = await call(
            session,
            "GetLoginData",
            LoginReq,
            {"account_id": account_id},
            # Подставь правильный тип ответа, если отличается от LoginRes
            # В Node у тебя было 'LoginRes', но по смыслу это может быть другой тип
            # Ниже — заглушка; используй реальный тип из proto
            LoginReq,  # <-- ЗАМЕНИТЬ на корректный тип ответа
            token,
        )
        print(f"\nGetLoginData status={ld['status']} len={ld['rawLen']} err={ld['err']}")
        print("  ->", json.dumps(pick(ld["decoded"], ["account_id", "nickname", "level", "exp", "coins", "gems", "region", "clan_id", "create_at"])))

        # 3) GetProfiles (authed)
        gp = await call(
            session,
            "GetProfiles",
            AvatarProfile,
            {},
            CSGetProfileListRes,
            token,
        )
        profs = gp["decoded"].get("profiles", []) if gp["decoded"] else []
        print(f"\nGetProfiles  status={gp['status']} len={gp['rawLen']} err={gp['err']}")
        selected = [p["avatar_id"] for p in profs if p.get("is_selected")]
        print(f"  -> profiles={len(profs)} selected={json.dumps(selected)}")

        # 4) GetWallet (authed)
        gw = await call(
            session,
            "GetWallet",
            CSGetWalletReq,
            {},
            CSGetWalletRes,
            token,
        )
        print(f"\nGetWallet    status={gw['status']} len={gw['rawLen']} err={gw['err']}")
        print("  ->", json.dumps(pick(gw["decoded"], ["account_id", "wallet"])))

        # 5) GetBackpack (authed)
        gb = await call(
            session,
            "GetBackpack",
            CSGetBackpackReq,
            {"is_login": True},
            CSGetBackpackRes,
            token,
        )
        items = gb["decoded"].get("items", []) if gb["decoded"] else []
        selected_avatar = None
        if gb["decoded"] and gb["decoded"].get("selected_items"):
            selected_avatar = gb["decoded"]["selected_items"].get("avatar_id")
        print(f"\nGetBackpack  status={gb['status']} len={gb['rawLen']} err={gb['err']}")
        print(f"  -> wallet={json.dumps(gb['decoded'].get('wallet'))} items={len(items)} selected_avatar={selected_avatar}")

        # 6) GetMailList (authed)
        gm = await call(
            session,
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
    asyncio.run(main())
