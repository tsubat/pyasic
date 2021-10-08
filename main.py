from network import MinerNetwork
import asyncio


async def main():
    miner_network = MinerNetwork('192.168.1.1')
    data = await miner_network.scan_network_for_miners()
    print(data)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
