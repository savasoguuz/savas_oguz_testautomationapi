![tests](https://github.com/savasoguuz/savas_oguz_testautomationapi/actions/workflows/tests.yml/badge.svg)

# savas_oguz_testautomationapi

Selenium (headless) ile Swagger Petstore API uçlarına yönelik **PET / STORE / USER** test otomasyonu.
- pytest + selenium + webdriver-manager
- Pozitif/negatif senaryolar
- Flaky demo API için retry ve toleranslar
- JUnit / HTML rapor desteği

## Çalıştırma
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q

nginx

