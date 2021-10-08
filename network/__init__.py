import netifaces
import ipaddress
import asyncio
from miners.miner_factory import MinerFactory

PING_RETRIES: int = 3
PING_TIMEOUT: int = 1


class MinerNetwork:
    def __init__(self, ip_addr=None):
        self.network = None
        self.miner_factory = MinerFactory()
        self.ip_addr = ip_addr
        self.connected_miners = {}

    def get_network(self):
        if self.network:
            return self.network
        gateways = netifaces.gateways()
        if not self.ip_addr:
            default_gateway = gateways['default'][netifaces.AF_INET][0]
        else:
            default_gateway = self.ip_addr
        subnet_mask = netifaces.ifaddresses(gateways['default'][netifaces.AF_INET][1])[netifaces.AF_INET][0]['netmask']
        return ipaddress.ip_network(f"{default_gateway}/{subnet_mask}", strict=False)

    async def scan_network_for_miners(self):
        local_network = self.get_network()
        print(f"Scanning {local_network} for miners...")
        scan_tasks = []
        for host in local_network.hosts():
            scan_tasks.append(self.ping_miner(host))
        miner_ips = await asyncio.gather(*scan_tasks)
        miner_ips = list(filter(None, miner_ips))
        print(f"Found {len(miner_ips)} connected miners...")
        create_miners_tasks = []
        for miner_ip in miner_ips:
            create_miners_tasks.append(self.miner_factory.get_miner(miner_ip))
        miners = await asyncio.gather(*create_miners_tasks)
        return miners

    async def ping_miner(self, ip: ipaddress.ip_address):
        for i in range(PING_RETRIES):
            connection_fut = asyncio.open_connection(str(ip), 4028)
            try:
                # get the read and write streams from the connection
                reader, writer = await asyncio.wait_for(connection_fut, timeout=PING_TIMEOUT)
                # immediately close connection, we know connection happened
                writer.close()
                # make sure the writer is closed
                await writer.wait_closed()
                # ping was successful
                return ip
            except asyncio.exceptions.TimeoutError:
                # ping failed if we time out
                continue
            except ConnectionRefusedError:
                # handle for other connection errors
                print("Unknown error...")
            # ping failed, likely with an exception
            except Exception as e:
                print(e)
            continue
        return
