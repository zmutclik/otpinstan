import httpx

OTPINSTAN_BASE = "https://otpinstan.com/api/reseller"


def _headers(api_key: str) -> dict:
    return {"X-Api-Key": api_key}


async def _api(endpoint: str, api_key: str, method: str = "GET",
               data: dict = None, params: dict = None, timeout: float = 30.0):
    headers = _headers(api_key)
    async with httpx.AsyncClient(timeout=timeout) as client:
        if method == "GET":
            resp = await client.get(
                f"{OTPINSTAN_BASE}/{endpoint}",
                headers=headers, params=params,
            )
        else:
            resp = await client.post(
                f"{OTPINSTAN_BASE}/{endpoint}",
                headers=headers, data=data,
            )
        resp.raise_for_status()
        return resp.json()


async def get_balance(api_key: str):
    return await _api("balance.php", api_key)


async def create_order(api_key: str, service: str, country: int,
                       server: str = "s5"):
    endpoint = "s5/order.php" if server == "s5" else "order.php"
    return await _api(endpoint, api_key, method="POST",
                      data={"service": service, "country": country})


async def check_order(api_key: str, order_id: str, server: str = "s5"):
    if server == "s5":
        endpoint = f"s5/check.php?order_id={order_id}"
    elif server == "s1":
        endpoint = f"s1/check.php?order_id={order_id}"
    else:
        endpoint = f"check.php?order_id={order_id}"
    return await _api(endpoint, api_key)


async def cancel_order(api_key: str, order_id: str, server: str = "s5"):
    if server == "s5":
        endpoint = "s5/cancel.php"
    elif server == "s1":
        endpoint = "s1/cancel.php"
    else:
        endpoint = "cancel.php"
    return await _api(endpoint, api_key, method="POST",
                      data={"order_id": order_id}, timeout=35.0)
