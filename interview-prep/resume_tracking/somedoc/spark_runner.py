from __future__ import annotations
import os
from copy import deepcopy
from typing import TYPE_CHECKING, Optional
import tempfile
import importlib.util
from datetime import datetime
import json
from collections import defaultdict

from uff.broadcast_value import pb_to_broadcast_value
from uff.utils.notebook_utils import is_jupyter
from uff.utils.display_utils import display_html, href
from uff.runners.runner import Runner

import uff.ir_pb2 as ir_pb2

if TYPE_CHECKING:
    from uff.pipeline import Pipeline


class SparkRunner(Runner):

    spark: SparkSession = None

    def __init__(
        self,
        spark_runner_conf: Optional[dict] = None,
        uff_jar: Optional[str] = None,
        additional_jars: Optional[list[str]] = None,
        cmk_path: Optional[str] = None,
        python_archive: Optional[str] = None,
        uff_ir_task_jar: Optional[str] = None,
    ):
        self.spark_runner_conf = spark_runner_conf
        self._check_gaia_id()
        self.uff_jar = uff_jar
        self.runner_mode = None
        self.additional_jars = additional_jars
        self.uff_ir_task_jar = uff_ir_task_jar
        self.cmk_path = cmk_path
        # (source_sample_ratio, current_date): (uid: df)
        self.persisted_dfs = defaultdict(dict)
        # to make spark source dataframes consistent (meaningful to persistence) within same session
        self.seen_pyspark_source_dfs = dict()
        if python_archive is not None:
            self.PYTHON_ARCHIVE = python_archive
        if is_jupyter():
            # to disable line wrapping on df.show(), and displays a horizontal scroll bar
            from IPython.core.display import HTML

            display(HTML("<style>pre { white-space: pre !important; }</style>"))
            # import spark related things AFTER and ONLY AFTER taiji_ide.set_spark!
            import taiji_ide

            taiji_ide.set_spark(
                version="3.3.1", gaia_id=str(self.spark_runner_conf["gaia_id"])
            )

    def _check_gaia_id(self):
        if self.spark_runner_conf is not None:
            if str(self.spark_runner_conf["gaia_id"]) in ("2938", "3122"):
                raise RuntimeError(
                    f"Gaia cluster with PPC architecture (天龙、鲸鱼) is not supported"
                )

    def init_jupyter_spark(
        self,
        gaia_id: str,
        group_id: str,
        cmk_path: str = None,
        spark_conf: dict[str, str] = None,
        uff_jar: str = None,
        additional_jars: list[str] = None,
        uff_ir_task_jar: str = None,
    ):
        if self.spark is None:
            # if is_jupyter(), set the messy things
            if is_jupyter():
                import taiji_ide

                if uff_jar is None:
                    uff_jar = self.BUILD_HDFS_PATH + "/" + "uff_main_spark33.fat.jar"
                print("Loading main jar: {}".format(uff_jar))

                if uff_ir_task_jar is None:
                    uff_ir_task_jar = self.BUILD_HDFS_PATH + "/uff_ir_task_main.fat.jar"
                print("Loading uff ir task jar: {}".format(uff_ir_task_jar))

                if additional_jars:
                    for j in additional_jars:
                        if "uff_main" in j.split("/")[-1]:
                            raise RuntimeError(
                                "Do not provide main jar in additional_jars, pass it via arg 'uff_jar'"
                            )
                        print("Loading additional jar: {}".format(j))

                os.environ["PYSPARK_SUBMIT_ARGS"] = "--jars {} pyspark-shell".format(
                    ",".join((additional_jars or list()) + [uff_jar, uff_ir_task_jar])
                )
                # only affects executor in notebook envrionment
                os.environ["PYSPARK_PYTHON"] = self.PYTHON

                os.environ["GAIA_ID"] = str(gaia_id)
                os.environ["GROUP_ID"] = group_id
                if cmk_path is not None:
                    taiji_ide.set_cmk(cmk_path)

                from pyspark.sql import SparkSession

                spark_session_builder = (
                    SparkSession.builder.enableHiveSupport()
                    # to avoid execution error java.lang.NumberFormatException: For input string: "30s"
                    # # https://mdnice.com/writing/d6681f3082f9449fa9a452c432acbd0d
                    .config("dfs.client.datanode-restart.timeout", 30)
                )

                _spark_conf = deepcopy(spark_conf or dict())
                default_conf = {
                    "spark.driver.memory": "2g",
                    "spark.executor.cores": 2,
                    "spark.executor.memory": "4g",
                    # only affects executor in notebook environment
                    "spark.yarn.dist.archives": self.PYTHON_ARCHIVE,
                    # faster file committing
                    "spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version": 2,
                    # open Adaptive Query Execution to automatically optimize skewed join
                    # https://spark.apache.org/docs/3.1.2/sql-performance-tuning.html#adaptive-query-execution
                    "spark.sql.adaptive.enabled": "true",
                    # this is true by default
                    "spark.sql.adaptive.coalescePartitions.enabled": "false",
                    # avoid listing leaf files which may take long time or even cause driver OOM
                    # (the conf name 'caseSensitiveInferenceMode' itself is case-sensitive :-D)
                    "spark.sql.hive.caseSensitiveInferenceMode": "never_infer",
                    # increase num partitions of join
                    "spark.sql.shuffle.partitions": 500,
                    # speculation
                    "spark.speculation": "true",
                    "spark.speculation.quantile": 0.9,
                    # to make session token mode works by loading packed special version of tdw toolkit
                    "spark.driver.userClassPathFirst": "true",
                    "spark.executor.userClassPathFirst": "true",
                    # iceberg confs
                    "hive.metastore.uris": "thrift://ss-qe-nginx-tauth.tencent-distribute.com:8106",
                    "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
                    "spark.sql.catalog.iceberg_catalog": "org.apache.iceberg.spark.SparkCatalog",
                    "spark.sql.catalog.iceberg_catalog.type": "hive",
                    "spark.sql.catalog.iceberg_catalog.uri": "thrift://ss-qe-nginx-tauth.tencent-distribute.com:8106",
                    "spark.sql.extensions": "org.apache.spark.sql.hudi.HoodieSparkSessionExtension,org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
                }
                for k, v in default_conf.items():
                    if k not in _spark_conf:
                        _spark_conf[k] = v

                for k, v in _spark_conf.items():
                    spark_session_builder.config(k, v)
                self.spark = spark_session_builder.getOrCreate()
            else:
                raise RuntimeError("Currently can only run in taiji Notebook!")
        return self

    def init_spark_taiji(self):
        # create spark session when running on taiji pyspark (not in notebook),
        # and leave spark confs to taiji workflow
        from pyspark.sql import SparkSession

        default_conf = {
            # iceberg&hudi confs
            "hive.metastore.uris": "thrift://ss-qe-nginx-tauth.tencent-distribute.com:8106",
            "spark.sql.catalog.spark_catalog": "org.apache.iceberg.spark.SparkSessionCatalog",
            "spark.sql.catalog.iceberg_catalog": "org.apache.iceberg.spark.SparkCatalog",
            "spark.sql.catalog.iceberg_catalog.type": "hive",
            "spark.sql.catalog.iceberg_catalog.uri": "thrift://ss-qe-nginx-tauth.tencent-distribute.com:8106",
            "spark.sql.extensions": "org.apache.spark.sql.hudi.HoodieSparkSessionExtension,org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions",
            # metric monitor
            "spark.extraListeners": "com.tencent.spark.metrics.SparkMetricsListener,gdt.rfc.uff.batch.BatchListener",
        }
        spark_session_builder = SparkSession.builder.enableHiveSupport()
        for k, v in default_conf.items():
            spark_session_builder.config(k, v)
        self.spark = spark_session_builder.getOrCreate()

    @property
    def spark_ui_url(self):
        return self.spark.sparkContext.uiWebUrl

    def get_data_view(
        self,
        pipeline: Pipeline,
        uid: str,
        options: dict = None,
        is_feature_group=False,
        is_sink_view=False,
    ):
        runner = self.execute_pipeline(pipeline, options=options)
        if is_feature_group:
            return runner.getFeatureGroup()
        elif is_sink_view:
            return runner.getSinkView(uid)
        else:
            return runner.getDataView(uid)

    def _get_runner_key(self, options: dict):
        return options["source_sample_ratio"], options["current_date"]

    def persist(
        self, pipeline: Pipeline, uid: str, options: dict = None, is_feature_group=False
    ):
        df = self.get_raw_df(pipeline, uid, options, is_feature_group)
        df.persist()
        self.persisted_dfs[self._get_runner_key(options)][uid] = df
        # trigger an action to perist immediately
        df.count()

    def unpersist(
        self, pipeline: Pipeline, uid: str, options: dict = None, is_feature_group=False
    ):
        df = self.get_raw_df(pipeline, uid, options, is_feature_group)
        df.unpersist()
        try:
            self.persisted_dfs[self._get_runner_key(options)].pop(uid)
        except:
            pass

    def unpersist_all(self):
        for runner_key, uid_to_dfs in self.persisted_dfs.items():
            for uid, df in uid_to_dfs.items():
                try:
                    df.unpersist()
                    print(f"Unpersisted: {uid}")
                except Exception as e:
                    print(f"Failed to unpersist {uid}: {e}")
        self.persisted_dfs.clear()

    def show(
        self,
        pipeline: Pipeline,
        uid: str,
        limit: int = 100,
        truncate: bool = False,
        options: dict = None,
        is_feature_group=False,
        is_sink_view=False,
        vertical=False,
    ):
        """
        Get a DataView and show it, will not return the df to user.
        """
        # dv = self.get_data_view(pipeline, uid, options, is_feature_group=is_feature_group)
        # df = dv.getDataFrame()
        # df.show(limit, truncate)
        df = self.get_raw_df(
            pipeline, uid, options, is_feature_group, is_sink_view=is_sink_view
        )
        df.show(limit, truncate, vertical=vertical)

    def get_raw_df(
        self,
        pipeline: Pipeline,
        uid: str,
        options: dict = None,
        is_feature_group=False,
        is_sink_view=False,
    ):
        """
        Returns a spark DataFrame, batch mode only.
        """
        if options.get("runner_mode", "").upper() == "BATCH":

            dv = self.get_data_view(
                pipeline,
                uid,
                options,
                is_feature_group=is_feature_group,
                is_sink_view=is_sink_view,
            )
            scala_df = dv.getDataFrame()

            # import goes here because we can only import pyspark after taiji_ide.set_spark()
            from pyspark.sql import DataFrame
            from pyspark.sql import SQLContext

            # sql_context = SQLContext(sparkContext=self.spark.sparkContext, sparkSession=self.spark)
            # convert to pyspark DataFrame, use SparkSession as 2th arg instead of sql_context, to avoid warning
            # of 'DataFrame constructor is internal. Do not directly use it.' in higher spark version
            return DataFrame(scala_df, self.spark)
        else:
            raise RuntimeError(
                'Only "batch" mode supports get_raw_df, please specify runner_mode of "batch" in options'
            )

    def has_udf(self, pipeline: Pipeline):
        return len(pipeline.data.udfs) > 0

    def has_pyspark_source(self, pipeline: Pipeline):
        return len(pipeline.data.pyspark_sources) > 0

    def prepare_source_dfs(self, pipeline: Pipeline, options: dict = None):
        """
        1st. assemble a sub pipeline that contains pyspark sources' upstream sources only
        2nd. execute the sub pipeline to get each source's DataFrame
        3rd. return a dict of [source.uid: DataFrame]
        """
        # import goes here because we can only import pyspark after taiji_ide.set_spark()
        from pyspark.sql import DataFrame
        from pyspark.sql import SQLContext

        # sql_context = SQLContext(sparkContext=self.spark.sparkContext, sparkSession=self.spark)

        pre_pyspark_pipeline = pipeline.get_pre_pyspark_pipeline()
        source_id_to_df = dict()

        sc = self.spark.sparkContext
        runner_factory = sc._jvm.gdt.rfc.uff.BatchRunnerFactory
        scala_options = sc._jvm.PythonUtils.toScalaMap(
            options or {"runner_mode": "batch"}
        )
        runner = runner_factory.getOrCreateRunner(scala_options)
        runner.evaluate(pre_pyspark_pipeline.meta_text)

        # todo: cache a source df if it is depended by more than one pyspark source?
        for s in pre_pyspark_pipeline.data.sources:
            dv = runner.getDataView(s.output_ids[0])
            scala_df = dv.getDataFrame()
            # convert to pyspark DataFrame, use SparkSession as 2th arg instead of sql_context, to avoid warning
            # of 'DataFrame constructor is internal. Do not directly use it.' in higher spark version
            source_id_to_df[s.uid] = DataFrame(scala_df, self.spark)
        return source_id_to_df

    def generate_pyspark_source_dfs(
        self, source_id_to_df, pipeline: Pipeline, options: dict
    ):
        """
        1st. for each pyspark source, execute its python function using SparkSession
            and upstream sources' result DataFrames
        2nd. return a dict of [pyspark_source.uid: DataFrame of the uid]
        """
        # prepare the function objects
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as tf:
            # import necessary libs
            tf.write("from pyspark.sql import DataFrame\n")
            tf.write("from pyspark.sql import SparkSession\n")
            tf.write("from datetime import *\n")
            # write function source code to a temporary module
            for pdf in pipeline.data.pyspark_source_funcs:
                tf.write(pdf.func_def)
                tf.write("\n")
            # import functions back into current process
            # reset cursor to head, as we are in the context
            tf.seek(0)
            spec = importlib.util.spec_from_file_location("pyspark_defs", tf.name)
            pyspark_defs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(pyspark_defs)

        current_date = options["current_date"]
        if isinstance(current_date, str):
            current_date = datetime.strptime(current_date, "%Y%m%d%H%M%S")
        print("Generating pyspark source on {}".format(current_date))

        pyspark_source_id_to_df = dict()
        for ps in pipeline.data.pyspark_sources:
            if ps.uid in self.seen_pyspark_source_dfs:
                pyspark_source_id_to_df[ps.uid] = self.seen_pyspark_source_dfs[ps.uid]
            else:
                # order matters!
                input_dfs = [source_id_to_df[sid] for sid in ps.input_ids]
                process_func = getattr(pyspark_defs, ps.func_name)
                user_kwargs = json.loads(ps.user_kwargs)
                pyspark_source_id_to_df[ps.uid] = process_func(
                    self.spark, current_date, *input_dfs, **user_kwargs
                )
                self.seen_pyspark_source_dfs[ps.uid] = pyspark_source_id_to_df[ps.uid]
        return pyspark_source_id_to_df

    def register_udfs(self, pipeline: Pipeline, options: dict = None):
        from pyspark.sql.types import (
            IntegerType,
            LongType,
            FloatType,
            DoubleType,
            BooleanType,
            StringType,
            ByteType,
            ArrayType,
        )

        data_type = ir_pb2.DataType
        return_type_map = {
            data_type.BOOL: BooleanType(),
            data_type.BOOL_ARRAY: ArrayType(BooleanType()),
            data_type.INT32: IntegerType(),
            data_type.INT32_ARRAY: ArrayType(IntegerType()),
            data_type.INT64: LongType(),
            data_type.INT64_ARRAY: ArrayType(LongType()),
            data_type.FLOAT: FloatType(),
            data_type.FLOAT_ARRAY: ArrayType(FloatType()),
            data_type.STRING: StringType(),
            data_type.STRING_ARRAY: ArrayType(StringType()),
            data_type.DOUBLE: DoubleType(),
            data_type.DOUBLE_ARRAY: ArrayType(DoubleType()),
            data_type.BYTE: ByteType(),
            data_type.BYTE_ARRAY: ArrayType(ByteType()),
        }
        from uff.runners.spark_type_utils import to_spark_type

        # prepare the function objects
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as tf:
            # write function source code to a temporary module
            for udf in pipeline.data.udfs:
                tf.write(udf.func_def)
                tf.write("\n")
            # import functions back into current process
            # reset cursor to head, as we are in the context
            tf.seek(0)
            spec = importlib.util.spec_from_file_location("udf_defs", tf.name)
            udf_defs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(udf_defs)

        for bc_value_msg in pipeline.data.broadcast_values:
            bc_value = pb_to_broadcast_value(bc_value_msg)
            print(
                "register broadcast_value {} to spark".format(bc_value.data.value_name)
            )
            local_value = bc_value._get_local_value_with_runner(pipeline, self, options)
            exec(
                "udf_defs.{} = self.spark.sparkContext.broadcast(local_value)".format(
                    bc_value.data.value_name
                )
            )

        for udf in pipeline.data.udfs:
            # now register udfs to SparkSession
            if udf.HasField("return_dtype"):
                # Take DType prior to DataType
                spark_return_type = to_spark_type(udf.return_dtype)
            else:
                if udf.return_type not in return_type_map:
                    raise RuntimeError(
                        "Unsupported return type: {}".format(udf.return_type)
                    )
                spark_return_type = return_type_map[udf.return_type]
            self.spark.udf.register(
                name=udf.func_name,
                f=getattr(udf_defs, udf.original_func_name),
                returnType=spark_return_type,
            )
            print("register udf {} to spark".format(udf.original_func_name))

    def init_spark(self):
        if is_jupyter():
            self.init_jupyter_spark(
                gaia_id=str(self.spark_runner_conf["gaia_id"]),
                group_id=str(self.spark_runner_conf["group_id"]),
                spark_conf=self.spark_runner_conf.get("spark_conf"),
                uff_jar=self.uff_jar,
                additional_jars=self.additional_jars,
                cmk_path=self.cmk_path,
                uff_ir_task_jar=self.uff_ir_task_jar,
            )
        else:
            self.init_spark_taiji()
        assert self.spark is not None, "SparkSession is None after init"

    def show_spark_url(self):
        # show Spark UI link on notebook execution
        from IPython.core.display import HTML

        display_html(href(self.spark_ui_url, "Spark UI"))

    def check_iceberg_table_exist(self, db: str, table: str) -> bool:
        self.init_spark()
        sc = self.spark.sparkContext
        iceberg_utils = sc._jvm.gdt.rfc.uff.batch.evaluator.IcebergUtils
        is_exist = iceberg_utils.tableExists(
            self.spark._jsparkSession, db + "." + table
        )
        return is_exist

    def load_iceberg_schema_json_str(self, db: str, table: str) -> str:
        self.init_spark()
        sc = self.spark.sparkContext
        iceberg_utils = sc._jvm.gdt.rfc.uff.batch.evaluator.IcebergUtils
        schema_json_str = iceberg_utils.loadSparkSchemaJsonStr(
            self.spark._jsparkSession, db + "." + table
        )
        return schema_json_str

    def resolve_source_field(
        self, column: str, pipeline: Pipeline, uid: str, options: dict = None
    ):
        dv = self.get_data_view(pipeline, uid, options, False)
        scala_df = dv.getDataFrame()

        sc = self.spark.sparkContext
        query_plan_utils = sc._jvm.gdt.rfc.uff.batch.utils.QueryPlanUtil
        source_fields = query_plan_utils.resolveSourceFieldFromDF(scala_df, column)
        return source_fields

    def execute_pipeline(self, pipeline: Pipeline, options: dict = None):
        if options.get("runner_mode", "").upper() == "BATCH":
            self.init_spark()
            if is_jupyter():
                # shows Spark UI link on every execution in notebook
                self.show_spark_url()
            if self.has_udf(pipeline):
                # register udfs to SparkSession
                self.register_udfs(pipeline, options)

            sc = self.spark.sparkContext
            runner_factory = sc._jvm.gdt.rfc.uff.BatchRunnerFactory
            scala_options = sc._jvm.PythonUtils.toScalaMap(
                options or {"runner_mode": "batch"}
            )

            if self.has_pyspark_source(pipeline):
                source_id_to_df = self.prepare_source_dfs(pipeline, options)
                pyspark_source_id_to_df = self.generate_pyspark_source_dfs(
                    source_id_to_df, pipeline, options
                )
                scala_input_dfs = sc._jvm.PythonUtils.toScalaMap(
                    {psid: pdf._jdf for psid, pdf in pyspark_source_id_to_df.items()}
                )
                runner = runner_factory.getOrCreateRunner(
                    scala_options, scala_input_dfs
                )
                runner.evaluate(pipeline.get_post_pyspark_pipeline().meta_text)
            else:
                runner = runner_factory.getOrCreateRunner(scala_options)
                runner.evaluate(pipeline.meta_text)
            return runner
        else:
            raise RuntimeError(
                'Currently only "batch" mode is supported, please specify runner_mode of "batch" in options'
            )

    def close(self):
        if self.spark is not None:
            self.spark.stop()
            self.spark = None
