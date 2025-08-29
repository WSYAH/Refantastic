from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union, Any
import networkx as nx
from networkx import DiGraph
from uff.materialized_view import SinkView
from uff.pipeline import Pipeline, get_source_pb
from uff.feature import FeatureGroup as LegacyFeatureGroup
from uff.data_collection import DataCollection
from uff.sink import LakeSink
# “X-stor” 是一个统一承载 CKV、CKV+ 等非关系型数据库服务 的平台
class Graph:
    @staticmethod
    def prune_to(
        pipeline: Pipeline,
        nodes: list[Union[DataCollection, LakeSink, LegacyFeatureGroup, str, SinkView]]
    ):
        # 将输入的 nodes 作为尾节点，去将 pipeline 剪枝形成一个新的 pipeline
        # 1. 将 pipeline 定义为一个 DAG，这样才更方便进行剪枝
        dag = Graph.pipeline_to_graph(pipeline)
        # 2. 然后剪枝DAG，仅仅保留和 nodes 相关联的边和节点
        target_nodes = [n.uid for n in nodes]
        broadcast_value_source_uids = [
            bc_value.source_data_uid for bc_value in pipeline.data.broadcast_values
        ]
        target_nodes.extend(broadcast_value_source_uids)
        pruned_nodes = set(target_nodes)
        for td in target_nodes:
            # 仅仅保留目标节点和他们的祖先
            pruned_nodes.update(nx.ancestors(dag,td))
        pruned_dag = dag.subgraph(pruned_nodes)
        # 生成一个新的 pipeline，当然不要忘了 UDF
        return Graph.graph_to_pipeline(pruned_dag, pipeline)

    @staticmethod
    def pipeline_to_graph(pipeline: Pipeline) -> DiGraph:
        dag = DiGraph()
        p = pipeline.data
        for source in p.sources:
            for out_id in source.output_ids:
                dag.add_edge(source.uid, out_id)
        # 然后相同的将 pyspark_sources、data_collections、transforms都操作一遍

        # 根据 Runner 的 protocol，并没有连接 data_collection->sink的edge，所以从 sink 侧去
        # 查找 data_collection->sink 的 edge。
        for sk in p.sinks:
            dag.add_edge(sk.input_id, sk.uid)
        # 然后相同的将 sink_views 和 feature_group都操作一遍
        return dag

    @staticmethod
    def graph_to_pipeline(dag: DiGraph, original_pipeline: Pipeline):
        new_pipeline = Pipeline(name=original_pipeline.data.name)
        new_pipeline.data.mode = original_pipeline.data.mode
        node_types = dict()
        # 然后定义新的、空的new_sources\pyspark_sources\data_collections\transforms\siks\feature_groups\sink_views
        # 以及 udfs\broadcast_values\pyspark_source_funcs\original_in_and_out_ids
        new_sources = dict()
        for nid in dag.nodes:
            source = get_source_pb(original_pipeline, nid)
            if source is not None:
                node_types[nid] = "source"
                new_source = ir_pb2.Source()
                new_source.ParseFromString(source.SerializeToString())
                del new_sources.output_ids[:]
                new_sources[nid] = new_source
                continue
            # 然后下面折叠了对 pyspark_source\data_collection\transform\sink\sink_view\feature_group的相同处理

        def get_new_node(nid: str):
            if node_types[nid] == "source":
                return new_sources[nid]
            # 其他类型也是相同处理，返回相对应的节点

        for edge in dag.edges:  # 在 pipeline 中按照 edge 连接新节点
            from_nid = edge[0]
            to_nid = edge[1]
            from_node = get_new_node(from_nid)
            to_node = get_new_node(to_nid)
            from_node.output_ids.append(to_nid)
            to_node.output_ids.append(from_nid)

        new_pipeline.data.sources.extend(new_sources.values())
        # 其他节点也挂载到 new_pipeine上
        return new_pipeline


