import base64, xxhash


def create_key_from_list(param_list, length_bytes=8, base64url=True, prefix="plwps:"):
    """
    Use this method in order to optimize the cache key generation using query params or any data.
    :param param_list:
    :param length_bytes:
    :param base64url:
    :param prefix:
    :return:
    """

    h64s = []
    for s in param_list:
        if not s:
            continue
        h64s.append(xxhash.xxh3_64_intdigest(s.strip().lower()))
    h64s = sorted(set(h64s))
    final = xxhash.xxh3_128()
    for v in h64s:
        final.update(v.to_bytes(8, "little", signed=False))
    raw = bytes.fromhex(final.hexdigest())[:length_bytes]
    out = base64.urlsafe_b64encode(raw).rstrip(b"=").decode() if base64url else raw.hex()
    return f"{prefix}{out}"
