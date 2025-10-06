from .helpers import BASE_URL, fetch_async, unique_id, eventually_status

def create_pet(driver):
    pid = unique_id()
    r = fetch_async(driver, "POST", f"{BASE_URL}/pet",
                    body={"id": pid, "name": f"S-{pid}", "photoUrls":["https://ex/p.jpg"], "status":"available"},
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] == 200
    return pid

def test_store_inventory(driver):
    r = fetch_async(driver, "GET", f"{BASE_URL}/store/inventory", headers={"Accept":"application/json"})
    assert r["status"] == 200 and isinstance(r["body"], dict)

def test_store_order_crud(driver):
    pid = create_pet(driver)
    oid = unique_id()
    order = {"id": oid, "petId": pid, "quantity": 1, "status":"placed", "complete": False}
    # create
    r = fetch_async(driver, "POST", f"{BASE_URL}/store/order",
                    body=order, headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] in (200, 201)

    # get
    r = eventually_status(driver, "GET", f"{BASE_URL}/store/order/{oid}", expect=(200, 201), timeout=10.0, interval=0.5)
    assert r["status"] in (200, 201), f"order get failed after retries: {r}"
    # 
    if isinstance(r["body"], dict):
        assert r["body"].get("id") == oid

    # delete
    r = fetch_async(driver, "DELETE", f"{BASE_URL}/store/order/{oid}", headers={"Accept":"application/json"})
    assert r["status"] == 200

    # confirm gone (eventual 404)
    r = eventually_status(driver, "GET", f"{BASE_URL}/store/order/{oid}", expect=404, timeout=10.0, interval=0.5)
    assert r["status"] == 404
