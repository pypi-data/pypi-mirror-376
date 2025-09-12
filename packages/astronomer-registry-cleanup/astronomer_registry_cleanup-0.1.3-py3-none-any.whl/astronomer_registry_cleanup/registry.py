import requests


def _parse_auth_challenge(header):
    if not header.startswith("Bearer "):
        raise ValueError(f"Unexpected auth challenge: {header}")
    params = {}
    parts = header[7:]
    for part in parts.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            params[key.strip()] = value.strip(' "')
    return params["realm"], params["service"], params["scope"]


def _exchange_basic_for_registry_token(auth_url, service, scope, username, password):
    params = {"service": service, "scope": scope, "account": username}
    r = requests.get(auth_url, auth=(username, password), params=params, timeout=30)
    if r.status_code == 200:
        d = r.json()
        t = d.get("token") or d.get("access_token")
        if t:
            return t
    r = requests.post(auth_url, auth=(username, password), data=params, timeout=30)
    if r.status_code == 200:
        d = r.json()
        return d.get("token") or d.get("access_token")
    r.raise_for_status()
    return None


def authenticated_get(url, username, password, timeout=600):
    username = username or "_"
    r = requests.get(url, timeout=timeout)
    if r.status_code != 401:
        if r.status_code == 200:
            return r
        r.raise_for_status()
    realm, service, scope = _parse_auth_challenge(r.headers.get("www-authenticate", ""))
    token = _exchange_basic_for_registry_token(realm, service, scope, username, password)
    if not token:
        raise ValueError("Failed to obtain registry token")
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
    r.raise_for_status()
    return r


def authenticated_delete(url, username, password, timeout=30):
    username = username or "_"
    r = requests.delete(url, timeout=timeout)
    if r.status_code != 401:
        if r.status_code in (200, 202, 204):
            return r
        r.raise_for_status()
    realm, service, scope = _parse_auth_challenge(r.headers.get("www-authenticate", ""))
    token = _exchange_basic_for_registry_token(realm, service, scope, username, password)
    if not token:
        raise ValueError("Failed to get registry token for DELETE")
    r = requests.delete(url, headers={"Authorization": f"Bearer {token}"}, timeout=timeout)
    r.raise_for_status()
    return r


def list_tags(registry, client, username, password):
    url = f"https://{registry}/v2/{client}/airflow/tags/list"
    resp = authenticated_get(url, username, password)
    data = resp.json()
    return data.get("tags", []) or []


def get_manifest_digest(registry, client, tag, username, password):
    url = f"https://{registry}/v2/{client}/airflow/manifests/{tag}"
    resp = authenticated_get(url, username, password)
    return resp.headers["Docker-Content-Digest"]


def delete_manifest(registry, client, digest, username, password):
    url = f"https://{registry}/v2/{client}/airflow/manifests/{digest}"
    authenticated_delete(url, username, password)


