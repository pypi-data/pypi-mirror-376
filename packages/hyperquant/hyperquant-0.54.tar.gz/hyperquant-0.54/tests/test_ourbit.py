import pybotters

from hyperquant.broker.ourbit import OurbitSpot
from hyperquant.broker.ourbit import OurbitSwap

async def download_orders():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEB3bf088f8b2f2fae07592fe1a6240e2d798100a9cb2a91f8fda1056b6865ab3ee"
            ]
        }
    ) as client:
        # 时间区间 (毫秒)
        start_time = 1757254540000   # 起始
        end_time = 1757433599999     # 结束

        page_size = 100              # 接口最大 100
        page_num = 1
        all_results = []

        while True:
            url = (
                "https://www.ourbit.com/api/platform/spot/deal/deals"
                f"?endTime={end_time}&pageNum={page_num}&pageSize={page_size}&startTime={start_time}"
            )
            res = await client.fetch("GET", url)
            result_list = res.data["data"]["resultList"]
            got = len(result_list)
            print(f"page {page_num} -> {got} items")
            all_results.extend(result_list)

            if got < page_size:      # 最后一页
                break
            page_num += 1

        print(f"total collected: {len(all_results)}")

        # 写入汇总数据
        import json
        with open("deals.json", "w") as f:
            json.dump(
                {
                    "data": {
                        "resultList": all_results,
                        "total": len(all_results),
                        "pageSize": page_size,
                        "pagesFetched": page_num
                    }
                },
                f,
                indent=2
            )
        print("Saved to deals.json")

async def test_detail():
    async with pybotters.Client() as client:
        ob = OurbitSpot(client)
        await ob.__aenter__()
        print(ob.store.detail.get({
            'name': 'OPEN'
        }))

async def test_ourbit_wrap():
    async with pybotters.Client(
        apis={
            "ourbit": [
                "WEB3bf088f8b2f2fae07592fe1a6240e2d798100a9cb2a91f8fda1056b6865ab3ee"
            ]
        }
    ) as client:
        ob = OurbitSwap(client)
        await ob.__aenter__()
        print(ob.store.detail.find())

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_detail())