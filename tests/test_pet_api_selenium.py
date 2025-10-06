import urllib.parse as urlenc
import pytest
from .helpers import BASE_URL, fetch_async, fetch_multipart, unique_id, eventually_status

# --- CRUD (POST/GET/PUT/DELETE) ---
def test_pet_crud_full(driver):
    pid = unique_id()
    create = {"id": pid, "name": f"Pet-{pid}", "photoUrls": ["https://ex/p.jpg"], "status": "available"}
    r = fetch_async(driver, "POST", f"{BASE_URL}/pet", body=create,
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] == 200 and r["body"]["id"] == pid

    # GET (eventual 200)
    r = eventually_status(driver, "GET", f"{BASE_URL}/pet/{pid}", expect=200)
    assert r["status"] == 200 and r["body"]["id"] == pid

    # PUT update
    upd = dict(create); upd["name"] += "-u"; upd["status"] = "sold"
    r = fetch_async(driver, "PUT", f"{BASE_URL}/pet", body=upd,
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] == 200 and r["body"]["name"].endswith("-u")

    # DELETE  
    r = fetch_async(driver, "DELETE", f"{BASE_URL}/pet/{pid}", headers={"Accept":"application/json"})
    assert r["status"] in (200, 404), f"Delete unexpected: {r}"

    # GET (eventual 404)
    r = eventually_status(driver, "GET", f"{BASE_URL}/pet/{pid}", expect=404)
    assert r["status"] == 404

# --- Negatifler ---
def test_pet_get_invalid_id(driver):
    r = fetch_async(driver, "GET", f"{BASE_URL}/pet/abc", headers={"Accept":"application/json"})
    assert r["status"] in (400, 404)

def test_pet_post_bad_body(driver):
    r = fetch_async(driver, "POST", f"{BASE_URL}/pet", body="not-json",
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] in (400, 405, 415, 500)

def test_pet_delete_nonexistent(driver):
    r = fetch_async(driver, "DELETE", f"{BASE_URL}/pet/999999999999", headers={"Accept":"application/json"})
    assert r["status"] in (404, 400)

# --- findByStatus & findByTags ---
@pytest.mark.parametrize("status", ["available","pending","sold"])
def test_pet_findByStatus(driver, status):
    r = fetch_async(driver, "GET", f"{BASE_URL}/pet/findByStatus?status={status}", headers={"Accept":"application/json"})
    assert r["status"] == 200 and isinstance(r["body"], list)

def test_pet_findByTags(driver):
    r = fetch_async(driver, "GET", f"{BASE_URL}/pet/findByTags?tags=cute", headers={"Accept":"application/json"})
    assert r["status"] in (200, 400, 404)
    if r["status"] == 200:
        assert isinstance(r["body"], list)

# --- POST /pet/{petId} form update ---
def test_pet_update_with_form(driver):
    pid = unique_id()
    # create
    r = fetch_async(driver, "POST", f"{BASE_URL}/pet",
                    body={"id": pid,"name": f"Form-{pid}","photoUrls":["https://ex/p.jpg"],"status":"available"},
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] == 200

    # form-update
    form = urlenc.urlencode({"name": f"Form-{pid}-u", "status": "sold"})
    r_form = fetch_async(driver, "POST", f"{BASE_URL}/pet/{pid}", body=form,
                         headers={"Content-Type":"application/x-www-form-urlencoded","Accept":"application/json"})

    if r_form["status"] in (200, 204):
        
        r = eventually_status(driver, "GET", f"{BASE_URL}/pet/{pid}", expect=200)
        assert r["status"] == 200
        assert r["body"]["name"] == f"Form-{pid}-u"
        assert r["body"]["status"] == "sold"
    else:
        
        assert r_form["status"] in (404, 405), f"Unexpected form update status: {r_form}"
        r = eventually_status(driver, "GET", f"{BASE_URL}/pet/{pid}", expect=(200, 404))
        if r["status"] == 200:
            
            assert r["body"]["id"] == pid
        else:
            
            assert r["status"] == 404

# --- uploadImage ---
def test_pet_upload_image(driver):
    pid = unique_id()
    r = fetch_async(driver, "POST", f"{BASE_URL}/pet",
                    body={"id": pid, "name": f"Up-{pid}", "photoUrls": ["https://ex/p.jpg"], "status": "available"},
                    headers={"Content-Type":"application/json","Accept":"application/json"})
    assert r["status"] == 200
    r = fetch_multipart(driver, "POST", f"{BASE_URL}/pet/{pid}/uploadImage",
                        fields={"additionalMetadata":"note"},
                        file_spec={"filename":"hi.txt","content":"hello","type":"text/plain"})
    assert r["status"] in (200, 204)
