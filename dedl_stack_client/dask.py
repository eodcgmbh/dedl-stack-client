from dask_gateway import Gateway
from distributed import Client
from contextlib import contextmanager


class DaskMultiCluster:
    gateway_registry = {
        "central": {
            "name": "Central Site",
            "address": "https://central.dedl.eodc.eu/dask",
            "proxy_address": "tcp://dask.central.dedl.eodc.eu:80",
            "default_config": {"min": 2, "max": 10},
        },
        "lumi": {
            "name": "LUMI Bridge",
            "address": "https://lumi.dedl.eodc.eu/dask",
            "proxy_address": "tcp://dask.lumi.dedl.eodc.eu:80",
            "default_config": {"min": 2, "max": 10},
        },
    }

    gateway = {}
    cluster = {}
    client = {}

    def __init__(self, auth):
        self.authenticator = auth
        for site in self.gateway_registry:
            # connect to gateway
            self.gateway[site] = Gateway(
                address=self.gateway_registry[site]["address"],
                proxy_address=self.gateway_registry[site]["proxy_address"],
                auth=self.authenticator,
            )

    def print_registry(self):
        print(self.gateway_registry)

    def get_gateways(self) -> None:
        for site in self.gateway_registry:
            print(f"{site}: {self.gateway_registry[site]}")

    def new_cluster(self, *args, **kwargs) -> None:
        for site in self.gateway_registry:
            # get new cluster object
            print(f"Create new cluster for {self.gateway_registry[site]['name']}")
            self.cluster[site] = self.gateway[site].new_cluster(*args, **kwargs)
            self.cluster[site].adapt(
                minimum=self.gateway_registry[site]["default_config"]["min"],
                maximum=self.gateway_registry[site]["default_config"]["max"],
            )
            self.client[site] = self.cluster[site].get_client(set_as_default=False)

    def compute(self, data, location_key: str = "location", **kwargs):
        return self.client[data.attrs[location_key]].compute(data, **kwargs)

    @contextmanager
    def as_current(self, location: str = "central") -> Client:
        yield self.client[location]

    def get_cluster_url(self):
        for site in self.gateway_registry:
            print(self.cluster[site].dashboard_link)

    def shutdown(self):
        for site in self.gateway_registry:
            self.cluster[site].close()
