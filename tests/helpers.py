import os, json, random, time
from typing import Any, Dict, Tuple

BASE_URL = os.getenv("BASE_URL", "https://petstore.swagger.io/v2")

def unique_id() -> int:
    return int(f"{int(time.time())}{random.randint(100,999)}")

def unique_name(prefix: str = "u") -> str:
    return f"{prefix}{int(time.time())}{random.randint(100,999)}"

def fetch_async(driver, method: str, url: str, body: Any = None, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Tarayıcıda fetch() çalıştırır. dict body -> JSON; str body -> ham.
    HER ZAMAN {"status": int, "ok": bool, "body": Any} sözlüğü döner.
    """
    if headers is None:
        headers = {}
    payload = json.dumps(body) if (body is not None and not isinstance(body, str)) else body
    script = """
      const done = arguments[arguments.length - 1];
      const method = arguments[0], url = arguments[1];
      const body = arguments[2], headers = arguments[3] || {};
      fetch(url, { method, headers, body })
        .then(async (res) => {
          let data; const ct = res.headers.get('content-type') || '';
          try { data = ct.includes('application/json') ? await res.json() : await res.text(); }
          catch (_) { data = null; }
          done({ status: res.status, ok: res.ok, body: data });
        })
        .catch(err => done({ status: 0, ok: false, body: String(err) }));
    """
    res = driver.execute_async_script(script, method, url, payload, headers)
    if isinstance(res, dict) and "status" in res:
        return res
    return {"status": 0, "ok": False, "body": None}

def fetch_multipart(driver, method: str, url: str, fields: Dict[str, str] | None = None,
                    file_spec: Dict[str, Any] | None = None, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    multipart/form-data upload. HER ZAMAN dict döner.
    """
    if headers is None:
        headers = {}
    script = """
      const done = arguments[arguments.length - 1];
      const method = arguments[0], url = arguments[1];
      const fields = arguments[2] || {}, fileSpec = arguments[3] || null, headers = arguments[4] || {};
      const fd = new FormData();
      for (const [k,v] of Object.entries(fields)) fd.append(k, v);
      if (fileSpec) {
        const blob = new Blob([fileSpec.content || ""], { type: fileSpec.type || "application/octet-stream" });
        fd.append("file", blob, fileSpec.filename || "upload.bin");
      }
      fetch(url, { method, headers, body: fd })
        .then(async (res) => {
          let data; const ct = res.headers.get('content-type') || '';
          try { data = ct.includes('application/json') ? await res.json() : await res.text(); }
          catch (_) { data = null; }
          done({ status: res.status, ok: res.ok, body: data });
        })
        .catch(err => done({ status: 0, ok: false, body: String(err) }));
    """
    res = driver.execute_async_script(script, method, url, fields or {}, file_spec or {}, headers)
    if isinstance(res, dict) and "status" in res:
        return res
    return {"status": 0, "ok": False, "body": None}

def eventually_status(driver, method: str, url: str, expect: int | Tuple[int, ...] = (200,),
                      timeout: float = 10.0, interval: float = 0.5,
                      headers: Dict[str, str] | None = None, body: Any = None) -> Dict[str, Any]:
    """
    Kısa retry'lı istek. HER ZAMAN dict döner (None asla değil).
    """
    if isinstance(expect, int):
        expect = (expect,)
    deadline = time.time() + timeout
    last: Dict[str, Any] = {"status": 0, "ok": False, "body": None}
    while time.time() < deadline:
        r = fetch_async(driver, method, url, body=body, headers=headers or {"Accept": "application/json"})
        if r.get("status") in expect:
            return r
        last = r
        time.sleep(interval)
    return last
