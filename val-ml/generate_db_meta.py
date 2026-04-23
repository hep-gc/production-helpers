from pydantic import BaseModel
from pathlib import Path
from typing import Dict, List
import rrdtool
from langchain_core.tools import tool

#-----------VARIABLES-----------------
DB_PATH = Path("/home/almalinux/rrds")


#CREATE METADATA
class MetricMeta(BaseModel):
    rrd_path: Path
    
class HostMeta(BaseModel):
    name: str
    cluster: str
    #path: Path
    metrics: Dict[str, MetricMeta]

class MetadataRegistry(BaseModel):
    clusters: Dict[str, List[HostMeta]]
    hosts: Dict[str, HostMeta]
    

def create_registry():
    """
    created a registry of the contents of an rrdtool db for LLM retrival.
    
    Args: 
        None
    
    Returns: 
        MetadataRegistry object
    """
    #1. get the clusters
    #2. for each cluster get host list
    #3. for each host get metric files
    registry = MetadataRegistry(clusters={}, hosts={})

    for cluster in DB_PATH.iterdir():
        if not cluster.is_dir() or cluster.name == "__SummaryInfo__":
            continue

        hosts = []
        for host in cluster.iterdir():
            if not host.is_dir() or host.name == "__SummaryInfo__":
                continue

            metrics={}
            for file in host.iterdir():
                if file.is_file() and file.suffix == ".rrd":
                    file_meta = MetricMeta(rrd_path=file, name=file.stem)
                    metrics[file.stem]= file_meta
                
            host_meta = HostMeta(name=host.name, cluster=cluster.name, metrics=metrics)
            registry.hosts[host.name] = host_meta
            hosts.append(host_meta)
        
        registry.clusters[cluster.name] = hosts
        
    return registry

