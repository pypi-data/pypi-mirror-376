def scrape():
    start = time.time()
    count = 0
    total_bytes_downloaded = 0

    while True:
        response = requests.get(api, headers=headers)
        try:
            data = response.json()
            items = data.get("itemList", [])

            items = [
                item for item in items
                if item.get("video", {}).get("downloadAddr") not in [None, "", "N/A"]
            ]

            count += len(items)

            for item in items:
                id = item.get("id")
                downloadAddr = item.get("video", {}).get("downloadAddr")

                try:
                    with requests.get(downloadAddr, headers=headers, stream=True, timeout=10) as r:
                        r.raise_for_status()
                        file_size = 0
                        file_path = os.path.join(folder, f"{id}.mp4")  
                        with open(file_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=32384):
                                if chunk:
                                    f.write(chunk)
                                    file_size += len(chunk)
                        total_bytes_downloaded += file_size

                        elapsed = time.time() - start
                        rate = count / elapsed if elapsed > 0 else 0
                        size_mb = total_bytes_downloaded / (1024 * 1024)

                        os.system('cls' if os.name == 'nt' else 'clear')
                        print(f"Average videos parsed & downloaded per second - {rate:.2f}/s")
                        print(f"Total size downloaded - {size_mb:.2f} MB")
                        print(f"Last STATUS Code - {response.status_code}")

                except requests.exceptions.RequestException:
                    pass

        except json.JSONDecodeError:
            print("Response is not valid JSON")
            print("Response length:", len(response.content))
            print("First 200 bytes:", response.content[:200])
