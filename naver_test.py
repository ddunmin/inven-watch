import requests

URL = "https://m.brand.naver.com/bugabookorea/products/11873046848"
UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")

r = requests.get(URL, headers={"User-Agent": UA}, timeout=(10, 30))
t = r.text
print("status:", r.status_code, "| length:", len(t))
print("has 블랙:", "블랙" in t)
print("has 품절:", "품절" in t)
print("has stockQuantity:", "stockQuantity" in t)
print("has optionCombinations:", "optionCombinations" in t)
print("--- 앞부분 ---")
print(t[:300])
