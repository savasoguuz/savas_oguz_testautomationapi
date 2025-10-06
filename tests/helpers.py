import os, json, random, time

BASE_URL = os.getenv("BASE_URL", "https://petstore.swagger.io/v2")

def unique_id() -> int:
    return int(f"{int(time.time())}{random.randint(100,999)}")

def unique_name(prefix="u") -> str:
    return f"{prefix}{int(time.time())}{random.randint(100,999)}"

def fetch_async(driver, method, url, body=None, headers=None):
    
    if headers is None: headers = {}
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
    return driver.execute_async_script(script, method, url, payload, headers)

def fetch_multipart(driver, method, url, fields=None, file_spec=None, headers=None):
    
    if headers is None: headers = {}
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
    return driver.execute_async_script(script, method, url, fields, file_spec, headers)

def eventually_status(driver, method, url, expect=(200,), timeout=10.0, interval=0.5, headers=None, body=None):
    
    if isinstance(expect, int): expect = (expect,)
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        r = fetch_async(driver, method, url, body=body, headers=headers or {"Accept":"application/json"})
        if r["status"] in expect:
            return r
        last = r
        time.sleep(interval)
    return last
