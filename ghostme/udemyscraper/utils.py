import logging

import httpx
from fp.fp import FreeProxy


class Super:
    def __init__(self, num_pages: int, proxy: bool = False) -> None:
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

        self.num_pages = num_pages
        self.proxy = proxy

    def generate_payloads(self) -> list[dict]:
        # make payloads to request different pages
        # we care about page number, everything else can stay the same
        lst = []
        for i in range(1, self.num_pages + 1):
            payload2 = self.payload.copy()
            payload2["page"] = i
            lst.append(payload2)

        return lst

    def make_post_request(self, client: httpx.Client, url: str, payload: dict) -> dict:
        # simple request
        request = client.post(url, json=payload)
        logging.info(request)   
        response = request.json()

        return response

    def make_get_request(
        self, client: httpx.Client, url: str, payload: dict = None
    ) -> dict:
        # simple request
        request = client.get(url)
        logging.info(request)
        response = request.json()

        return response

    def generate_proxy(self):
        proxy_object = FreeProxy(rand=True, timeout=1, elite=True, https=True)
        logging.info(f"gathering proxies")
        proxy = proxy_object.get()
        logging.info(f"proxy address {proxy}")

        return proxy
