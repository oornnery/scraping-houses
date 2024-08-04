import httpx


def get_client():
    return httpx.Client()


def get_async_client():
    with httpx.AsyncClient() as client:
        yield client
