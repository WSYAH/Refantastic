"""
Oceanus does not support PyFlink.
So this FlinkRunner currently Operates Flink jobs on Oceanus to provide conveniences for testing.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
import os
import json
from copy import deepcopy
from datetime import datetime
import tempfile
import importlib.util
import shutil
from enum import Enum
import time

import pandas as pd

from uff.runners.runner import Runner
from uff.utils.oceanus_api import OceanusApi
from uff.utils.file_utils import notebook_hdfs_client, zip_file
from uff.utils.notebook_utils import is_jupyter, notebook_util
from uff.utils.display_utils import (
    DisplayFullDataFrame,
    href,
    display_html,
    display_msg,
)

if TYPE_CHECKING:
    from uff.pipeline import Pipeline


class FlinkRunner(Runner):
    """
    Oceanus API:
    Project
        File
        Job
            JarFileId
            ArtifactFileId
    """

    class OceanusUFFConstants:
        # 'RFC测试'项目，使用 g_sng_gdt_rfc_platform 应用组
        TEST_PROJECT_ID = 14183
        # 测试用峰峦集群, fengluan-cdg-ams-on-off-sz-flink1
        # CLUSTER_ID = 20220
        # yarn-cdg-common-ss-flink-2
        CLUSTER_ID = 20214
        FLINK_VERSION = "1.15"
        JOB_TYPE = "JAR"
        CONTENT_UNDERSTAND_TEMPLATE_JOB_ID = 161151
        TEMPLATE_JOB_ID = 161152

    # https://iwiki.woa.com/p/1324781785#1.4-%E4%BD%9C%E4%B8%9A%E7%8A%B6%E6%80%81%E8%A1%A8
    class JobStatus(Enum):
        # UNKNOWN is not an oceanus status, it is used to indicate a start point of polling job status
        UNKNOWN = "UNKNOWN"
        READY = "READY"
        UNREADY = "UNREADY"
        SUBMITTING = "SUBMITTING"
        LAUNCHING = "LAUNCHING"
        RUNNING = "RUNNING"
        RESTARTING = "RESTARTING"
        CANCELLING = "CANCELLING"
        CANCELLED = "CANCELLED"
        FAILING = "FAILING"
        RECOVERING = "RECOVERING"
        FAILED = "FAILED"
        FINISHED = "FINISHED"

    # DEFAULT_MAIN_JAR = Runner.BUILD_HDFS_PATH + '/' + 'uff_stream_main.fat.jar'
    MAIN_CLASS_NAME = "gdt.rfc.uff.RunnerMain"
    BASE_SHOW_DATA_PATH = "hdfs://ss-cdg-16-v3/data/MAPREDUCE/CDG/g_sng_gdt_dw/dev/data/rfc/uff/stream_show"
    # assigned on interaction by framework, should not be overridden by template args or user options
    PROTECTED_ARGS = (
        "resource_config",
        "irFile",
        "env",
        "runner_mode",
        "source_sample_ratio",
        "current_date",
        "stream_sink_record_count",
        "stream_sink_path",
        "only_output_schema",
        "printSinkView",
        "is_sink_open",
        "is_show_open",
    )

    class Paginator:

        def __init__(self, page_size: int):
            self.page_size = page_size

        def paginate(self, current_page_num: int, total_size: int):
            if current_page_num * self.page_size < total_size:
                return current_page_num + 1
            else:
                return -1

    def __init__(
        self,
        file_dir: Optional[str] = None,
        uff_jar: Optional[str] = None,
        flink_runner_conf: Optional[dict] = None,
    ):
        self.user_home = notebook_util.get_user_home()
        self.cmk_path = self.user_home + "/cmk.json"
        self.cmk: dict = None
        self.oceanus = None
        self.user = "UFF"
        self.jar_is_specified = uff_jar is not None
        self.uff_jar = uff_jar
        # temp files location
        self.file_dir = (
            self.user_home + "/" + "_uff_tmp/stream" if file_dir is None else file_dir
        )
        self.job_name = "uff_test_" + datetime.now().strftime("%Y-%m-%d")
        self.flink_runner_conf = (
            flink_runner_conf if flink_runner_conf is not None else {}
        )

        if is_jupyter():
            os.makedirs(self.file_dir, exist_ok=True)
            self.init_cmk()
            self.oceanus = OceanusApi(user=self.cmk["subject"], cmk=self.cmk["key"])

            self.user = notebook_util.get_current_user()
            self.job_name = f"{self.user}_{self.job_name}"
            # remove these environment variables to use our specified hadoop client.
            # (taiji_ide.set_spark changes them to corresponding gaia versions, normally there should be
            # only one env per kernel and kernels are different processes,
            # but just clear them to make sure hour self.hadoop_bin works)
            # 'HADOOP_HOME': '/opt/tdw/tdwgaia2.8',
            # 'HADOOP_CONF_DIR': '/opt/tdw/gaia-cluster/3810'}
            for k in ("HADOOP_HOME", "HADOOP_CONF_DIR"):
                if k in os.environ:
                    os.environ.pop(k)
            self.hadoop_bin = "/opt/tdw/tdwgaia3.2/bin/hadoop"

    def init_cmk(self):
        with open(self.cmk_path, "r") as f:
            self.cmk = json.loads(f.readline())

    def find_job_by_name(self, job_name, project_id: int) -> Optional[dict, None]:
        paginator = self.Paginator(page_size=20)
        current_page_num = paginator.paginate(0, 1000000)
        while current_page_num > 0:
            resp = self.oceanus.get_job_list(
                keyword=job_name,
                project_id=project_id,
                page_num=current_page_num,
                page_size=paginator.page_size,
            )
            for job in resp["pageElements"]:
                if job["name"] == job_name:
                    return job
            current_page_num = paginator.paginate(current_page_num, resp["totalSize"])
        return None

    def create_job(self, job_name, project_id: int) -> dict:
        return self.oceanus.create_job(
            project_id=project_id,
            name=job_name,
            job_type=self.OceanusUFFConstants.JOB_TYPE,
            flink_version=self.OceanusUFFConstants.FLINK_VERSION,
            description=f"UFF stream job {self.user}",
        )

    def upload_file(self, project_id: int, file_path: str) -> dict:
        _, extension = os.path.splitext(file_path)
        f_name = os.path.basename(file_path)
        f_name_on_oceanus = (
            f_name[: -len(extension)]
            + "."
            + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            + extension
        )
        return self.oceanus.upload_file(
            project_id=project_id,
            file_path=file_path,
            description=f"Uff stream job {self.user}",
            file_name=f_name_on_oceanus,
        )

    def prepare_jar(self, file_path: str):
        if not file_path.endswith(".jar"):
            raise RuntimeError('A jar file name must end with ".jar"')
        local_path = self.file_dir + "/" + os.path.basename(file_path)
        if file_path.startswith("hdfs://"):
            notebook_hdfs_client.download(file_path, dest_path=local_path, force=True)
        else:
            shutil.copy(file_path, local_path)
        return local_path

    def get_ir_file_name(self, job_name) -> str:
        return self.file_dir + "/" + job_name + ".pbtxt"

    def prepare_ir_file(self, pipeline: Pipeline, job_name) -> str:
        f_path = self.get_ir_file_name(job_name)
        zipped_path = f_path + ".zip"
        with open(f_path, "w") as raw_f:
            raw_f.write(pipeline.meta_text)
        zip_file(f_path, zipped_path, arc_name=os.path.basename(f_path))
        return zipped_path

    def get_latest_file_version(self, file_name):
        # the Oceanus API returns in a desc order by version, just take the first result
        _file = self.find_file_by_name(file_name)
        if not _file:
            raise RuntimeError(f"file not exist on Oceanus: {file_name}")
        resp = self.oceanus.get_file_version_list(
            file_id=_file["id"], project_id=self.OceanusUFFConstants.TEST_PROJECT_ID
        )
        return _file["id"], resp["pageElements"][0]["version"]

    def find_file_by_name(self, file_name):
        paginator = self.Paginator(page_size=20)
        current_page_num = paginator.paginate(0, 1000000)
        while current_page_num > 0:
            resp = self.oceanus.get_file_list(
                keyword=file_name,
                project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                page_num=current_page_num,
                page_size=paginator.page_size,
            )
            for f in resp["pageElements"]:
                if f["name"] == file_name:
                    return f
            current_page_num = paginator.paginate(current_page_num, resp["totalSize"])
        return None

    def assemble_program(
        self,
        job_name: str,
        stream_sink_path: str,
        limit: int = 100,
        jar_file: dict = None,
        ir_file: dict = None,
        artifacts: dict = None,
        options: dict = None,
    ) -> dict:
        options = dict() if options is None else options
        jar_file_version = (
            {
                "projectId": jar_file["project"]["id"],
                "fileId": jar_file["id"],
                "version": jar_file["currentVersion"],
            }
            if jar_file is not None
            else None
        )
        # note the leading slash
        args = {
            "irFile": "/" + os.path.basename(self.get_ir_file_name(job_name)),
            # only dev is allowed
            "env": "dev",
            "runner_mode": "stream",
            "source_sample_ratio": options.get("source_sample_ratio") or 0.05,
            # scala translation need current_date to replace wildcards, set current_data to avoid exception
            "current_date": options.get("current_date")
            or datetime.now().strftime("%Y%m%d000000"),
            "stream_sink_record_count": limit,
            "stream_sink_path": stream_sink_path,
            "only_output_schema": (
                options.get("only_output_schema") or "false"
            ).lower(),
            "printSinkView": (options.get("printSinkView") or "false").lower(),
            "is_sink_open": (options.get("is_sink_open") or "false").lower(),
            "is_show_open": (options.get("is_show_open") or "false").lower(),
        }

        # extra options for some special cases
        for k, v in options.items():
            if k not in self.PROTECTED_ARGS:
                args[k] = v

        arguments = "\n".join([f"{k}={v}" for k, v in args.items()])

        # get latest file version of python venv artifact
        # venv_file_id_version = self.get_latest_file_version('uff_stream_py39_ad_pemja.zip')

        artifact_file_versions = (
            deepcopy(artifacts) if artifacts is not None else dict()
        )
        if ir_file is not None:
            artifact_file_versions.update(
                {
                    ir_file["name"]: {
                        "projectId": ir_file["project"]["id"],
                        "fileId": ir_file["id"],
                        "version": ir_file["currentVersion"],
                    }
                }
            )

        if "extra_artifact_files" in self.flink_runner_conf:
            extra_artifact_files = self.flink_runner_conf.get("extra_artifact_files")
            print("adding artifact files:", extra_artifact_files)
            if artifact_file_versions is None:
                artifact_file_versions = extra_artifact_files
            else:
                artifact_file_versions = artifact_file_versions | extra_artifact_files
        res = {
            "type": "jar",
            "mainClassName": self.MAIN_CLASS_NAME,
            "arguments": arguments,
            "platformJars": [],
        }
        if jar_file_version is not None:
            res["jarFileVersion"] = jar_file_version
        if artifact_file_versions is not None:
            res["artifactFileVersions"] = artifact_file_versions
        return res

    def show_job_url(self, job_id):
        oceanus_url = f"https://oceanus.woa.com/#/task/streaming/detail/{self.OceanusUFFConstants.TEST_PROJECT_ID}/{job_id}/edit"
        if is_jupyter():
            display_html(href(oceanus_url, "Oceanus UI"))
        else:
            print(f"Oceanus UI：{oceanus_url}")

    def upload_jar_file(self, jar_path: str, project_id: int) -> dict:
        jar_file_path = self.prepare_jar(jar_path)
        jar_file = self.upload_file(project_id, jar_file_path)
        return jar_file

    def upload_ir_file(
        self, pipeline: Pipeline, project_id: int, job_name: str
    ) -> dict:
        ir_path = self.prepare_ir_file(pipeline, job_name)
        ir_file = self.upload_file(project_id, ir_path)
        return ir_file

    def get_template_job_id(self, pipeline: Pipeline) -> int:
        if pipeline.is_content_understand:
            return FlinkRunner.OceanusUFFConstants.CONTENT_UNDERSTAND_TEMPLATE_JOB_ID
        return FlinkRunner.OceanusUFFConstants.TEMPLATE_JOB_ID

    def get_template_job_manifest(self, pipeline: Pipeline) -> dict:
        job_id = self.get_template_job_id(pipeline)
        return self.oceanus.get_job_manifest(
            FlinkRunner.OceanusUFFConstants.TEST_PROJECT_ID, job_id
        )

    def get_template_job_resource(self, pipeline: Pipeline) -> dict:
        job_id = self.get_template_job_id(pipeline)
        return self.oceanus.get_job_resource(
            FlinkRunner.OceanusUFFConstants.TEST_PROJECT_ID, job_id
        )

    def get_template_job_resource_post_args(self, pipeline: Pipeline) -> dict:
        """Oceanus returns like:
        {'cluster': {'id': 20214,
             'name': 'yarn-cdg-common-ss-flink-2',
             'online': True,
             'projectId': 0,
             'type': 'YARN'},
         'cpuCores': 17,
         'cpuCoresPerTaskmanager': 4,
         'createTime': 1734346197830,
         'creator': 'jansonliu',
         'description': '',
         'id': 3,
         'job': {'id': 161442,
                 'name': 'jansonliu_uff_test_2024-12-13',
                 'projectId': 14183},
         'jobmanagerCpuCores': 1,
         'jobmanagerMemoryBytes': 4294967296,
         'maxParallelism': 8192,
         'memoryBytes': 38654705664,
         'memoryBytesPerTaskmanager': 8589934592,
         'parallelismPerCore': 1.0}
        """
        raw = self.get_template_job_resource(pipeline)
        return {
            "cluster_id": raw["cluster"]["id"],
            "jobmanager_cpu_cores": raw["jobmanagerCpuCores"],
            "jobmanager_memory_bytes": raw["jobmanagerMemoryBytes"],
            "cpu_cores_per_taskmanager": raw["cpuCoresPerTaskmanager"],
            "max_parallelism": raw["maxParallelism"],
            "parallelism_per_core": raw["parallelismPerCore"],
            "memory_bytes_per_taskmanager": raw["memoryBytesPerTaskmanager"],
            "cpu_cores": raw["cpuCores"],
            "memory_bytes": raw["memoryBytes"],
        }

    def extract_jar_file_from_job_manifest(self, job_manifest: dict) -> dict:
        """
        converts jar_file of job_manifest returned by API to format used for posting
        """
        jar_file_version = job_manifest["program"]["jarFileVersion"]
        """
        e.g.: 
        'jarFileVersion': {'projectId': 11100, 'fileId': 127985, 'version': 1}
        """
        jar_file = {
            "project": {"id": jar_file_version["projectId"]},
            "id": jar_file_version["fileId"],
            "currentVersion": jar_file_version["version"],
        }
        return jar_file

    def create_or_update_job(
        self,
        pipeline: Pipeline,
        stream_sink_path: str,
        limit: int = 100,
        job_name: str = None,
        main_jar: str = None,
        options: dict = None,
    ) -> dict:
        options = dict() if options is None else options
        actual_job_name = job_name if job_name is not None else self.job_name

        env = options.get("env") or "dev"
        if env.lower() == "dev":
            project_id = self.OceanusUFFConstants.TEST_PROJECT_ID
        else:
            raise Exception("Can only launch job in RFCDev project")
        main_jar_path = main_jar if main_jar is not None else self.uff_jar

        template_job_manifest = self.get_template_job_manifest(pipeline)
        force_upload_jar = (
            str(options.get("force_upload_jar") or "false").lower() == "true"
        )

        # add template args to options
        template_args = [
            (line.split("=")[0].strip(), line.split("=")[1].strip())
            for line in template_job_manifest["program"]["arguments"].split("\n")
        ]
        # priorities, 0 for highest:
        # 0: protected args assigned by framework in method assemble_program
        # 1: user specified options
        # 2: template args
        template_options = {
            k: v
            for k, v in template_args
            if not k.startswith("#")
            and k not in self.PROTECTED_ARGS
            and k not in options
        }
        merged_options_for_first_running = deepcopy(options)
        merged_options_for_first_running.update(template_options)

        existed_job = self.find_job_by_name(actual_job_name, project_id)
        if existed_job is not None:
            print(
                f"Application {actual_job_name} already exist on Oceanus, updating it"
            )
            job = existed_job
            status = self.get_job_status(job["id"])
            template_jar_file = self.extract_jar_file_from_job_manifest(
                template_job_manifest
            )
            if status != self.JobStatus.UNREADY:
                if force_upload_jar:
                    if not self.jar_is_specified:
                        raise RuntimeError(
                            "please specify uff_jar in env to force upload jar"
                        )
                    print(f"Uploading jar file from: {main_jar_path}")
                    jar_file = self.upload_jar_file(
                        main_jar_path, self.OceanusUFFConstants.TEST_PROJECT_ID
                    )
                elif self.jar_is_specified:
                    job_manifest = self.oceanus.get_job_manifest(
                        project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                        job_id=job["id"],
                    )
                    jar_file = self.extract_jar_file_from_job_manifest(job_manifest)
                    if template_jar_file["id"] == jar_file["id"]:
                        print(f"Uploading jar file from: {main_jar_path}")
                        jar_file = self.upload_jar_file(
                            main_jar_path, self.OceanusUFFConstants.TEST_PROJECT_ID
                        )
                else:
                    # use template jar
                    jar_file = self.extract_jar_file_from_job_manifest(
                        template_job_manifest
                    )

                job_manifest = self.oceanus.get_job_manifest(
                    project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                    job_id=job["id"],
                )
                # add job args to options
                job_args = [
                    (line.split("=")[0].strip(), line.split("=")[1].strip())
                    for line in job_manifest["program"]["arguments"].split("\n")
                ]
                # priorities, 0 for highest:
                # 0: protected args assigned by framework in method assemble_program
                # 1: user specified options
                # 2: job args
                job_options = {
                    k: v
                    for k, v in job_args
                    if not k.startswith("#")
                    and k not in self.PROTECTED_ARGS
                    and k not in options
                }
                merged_options = deepcopy(options)
                merged_options.update(job_options)

                template_artifacts = template_job_manifest["program"][
                    "artifactFileVersions"
                ]

                print("Updating ir file")
                ir_file = self.upload_ir_file(
                    pipeline, self.OceanusUFFConstants.TEST_PROJECT_ID, actual_job_name
                )

                program = self.assemble_program(
                    job_name=actual_job_name,
                    stream_sink_path=stream_sink_path,
                    jar_file=jar_file,
                    ir_file=ir_file,
                    limit=limit,
                    artifacts=template_artifacts,
                    options=merged_options,
                )
                self.oceanus.create_update_job_manifest(
                    project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                    job_id=job["id"],
                    program=program,
                    new_version=True,
                    apply=True,
                )
                if "resource_config" in options:
                    template_resource = self.get_template_job_resource_post_args(
                        pipeline
                    )
                    final_job_resource = deepcopy(template_resource)
                    for k, v in options["resource_config"].items():
                        final_job_resource[k] = v
                    display_msg("更新任务资源: {}".format(final_job_resource), "INFO")
                    self.oceanus.update_job_resource(
                        project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                        job_id=job["id"],
                        description=f"UFF stream job initial resource {self.user}",
                        **final_job_resource,
                    )

            else:
                # job is in unready status unexpectedly
                print(
                    f"Application {actual_job_name} is in unready status unexpectedly, updating it"
                )
                if self.jar_is_specified:
                    print(f"Uploading jar file from: {main_jar_path}")
                    jar_file = self.upload_jar_file(
                        main_jar_path, self.OceanusUFFConstants.TEST_PROJECT_ID
                    )
                else:
                    jar_file = self.extract_jar_file_from_job_manifest(
                        template_job_manifest
                    )
                template_artifacts = template_job_manifest["program"][
                    "artifactFileVersions"
                ]
                print("Uploading ir file")
                ir_file = self.upload_ir_file(
                    pipeline, self.OceanusUFFConstants.TEST_PROJECT_ID, actual_job_name
                )

                # use template configuration
                template_conf = template_job_manifest["configuration"]

                program = self.assemble_program(
                    job_name=actual_job_name,
                    stream_sink_path=stream_sink_path,
                    jar_file=jar_file,
                    ir_file=ir_file,
                    limit=limit,
                    artifacts=template_artifacts,
                    options=merged_options_for_first_running,
                )
                self.oceanus.create_update_job_manifest(
                    project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                    job_id=job["id"],
                    program=program,
                    new_version=True,
                    apply=True,
                    configuration=template_conf,
                )
                # use template resource
                template_resource = self.get_template_job_resource_post_args(pipeline)
                final_job_resource = deepcopy(template_resource)
                if "resource_config" in options:
                    for k, v in options["resource_config"].items():
                        final_job_resource[k] = v
                display_msg("更新任务资源: {}".format(final_job_resource), "INFO")
                self.oceanus.update_job_resource(
                    project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                    job_id=job["id"],
                    description=f"UFF stream job initial resource {self.user}",
                    **final_job_resource,
                )
        else:
            # create a new job
            print(f"Creating Oceanus application: {actual_job_name}")
            job = self.create_job(actual_job_name, project_id)

            if self.jar_is_specified:
                print(f"Uploading jar file from: {main_jar_path}")
                jar_file = self.upload_jar_file(
                    main_jar_path, self.OceanusUFFConstants.TEST_PROJECT_ID
                )
            else:
                jar_file = self.extract_jar_file_from_job_manifest(
                    template_job_manifest
                )
            template_artifacts = template_job_manifest["program"][
                "artifactFileVersions"
            ]

            print("Uploading ir file")
            ir_file = self.upload_ir_file(
                pipeline, self.OceanusUFFConstants.TEST_PROJECT_ID, actual_job_name
            )

            # use template configuration
            template_conf = template_job_manifest["configuration"]

            program = self.assemble_program(
                job_name=actual_job_name,
                stream_sink_path=stream_sink_path,
                jar_file=jar_file,
                ir_file=ir_file,
                limit=limit,
                artifacts=template_artifacts,
                options=merged_options_for_first_running,
            )
            self.oceanus.create_update_job_manifest(
                project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                job_id=job["id"],
                program=program,
                new_version=True,
                apply=True,
                configuration=template_conf,
            )
            # use template resource
            template_resource = self.get_template_job_resource_post_args(pipeline)
            self.oceanus.update_job_resource(
                project_id=self.OceanusUFFConstants.TEST_PROJECT_ID,
                job_id=job["id"],
                description=f"UFF stream job initial resource {self.user}",
                **template_resource,
            )

        print(f"Oceanus job {actual_job_name} configured.")
        return job

    def poll_job_status(
        self,
        job_id: int,
        target_statuses: list[JobStatus],
        interval: int = 10,
        try_limit: int = 30,
    ) -> (bool, JobStatus):
        target_vals = [ts.value for ts in target_statuses]
        try_cnt = 0
        status = "UNKNOWN"
        while status not in target_vals and try_cnt < try_limit:
            js = self.oceanus.get_job_info(
                self.OceanusUFFConstants.TEST_PROJECT_ID, job_id
            )
            status = js["state"]
            if status in target_vals:
                return True, self.JobStatus(status)
            else:
                time.sleep(interval)
                try_cnt += 1
        else:
            return False, self.JobStatus(status)

    def get_job_status(self, job_id: int) -> JobStatus:
        job_info = self.oceanus.get_job_info(
            self.OceanusUFFConstants.TEST_PROJECT_ID, job_id
        )
        return self.JobStatus(job_info["state"])

    def start_or_restart_job(self, job_id: int):
        job_info = self.oceanus.get_job_info(
            self.OceanusUFFConstants.TEST_PROJECT_ID, job_id
        )
        statuses_need_to_stop = [
            self.JobStatus.RUNNING,
            self.JobStatus.FAILING,
            self.JobStatus.LAUNCHING,
            self.JobStatus.RECOVERING,
            self.JobStatus.RESTARTING,
            self.JobStatus.SUBMITTING,
        ]
        statuses_need_to_wait = [self.JobStatus.CANCELLING]
        statuses_can_start = [
            self.JobStatus.CANCELLED,
            self.JobStatus.FAILED,
            self.JobStatus.READY,
            self.JobStatus.FINISHED,
        ]
        job_status = self.JobStatus(job_info["state"])
        polled_status = None
        can_start = False
        if job_status in statuses_need_to_stop:
            print(f"Application status: {job_status.value}, stopping it")
            self.oceanus.stop_job(self.OceanusUFFConstants.TEST_PROJECT_ID, job_id)
            can_start, polled_status = self.poll_job_status(
                job_id, statuses_can_start, interval=10, try_limit=100
            )
        elif job_status in statuses_need_to_wait:
            print(f"Application status: {job_status.value}, waiting it to stop")
            can_start, polled_status = self.poll_job_status(
                job_id, statuses_can_start, interval=10, try_limit=100
            )
        elif job_status in statuses_can_start:
            can_start = True

        if can_start:
            print("Starting the job.")
            self.oceanus.start_job(self.OceanusUFFConstants.TEST_PROJECT_ID, job_id)
        else:
            self.show_job_url(job_id)
            raise RuntimeError(
                "Cannot start job properly, please stop the job on Oceanus manually."
            )

    def get_show_data_path(self, uid: str):
        now = datetime.now()
        return (
            self.BASE_SHOW_DATA_PATH
            + "/"
            + now.strftime("%Y%m%d")
            + "/"
            + now.strftime("%Y%m%d%H%M%S")
            + "/"
            + uid
        )

    def get_show_result(self, show_data_path: str, limit: int = 100) -> list[str]:
        res = list()
        file_paths = notebook_hdfs_client.list_files(show_data_path)
        for fp in file_paths:
            if len(res) >= limit:
                break
            # there may be more than one result files
            lines = notebook_hdfs_client.read_file(fp, head_count=limit - len(res))
            # the result row starts with '+I[' and ends with ']', just strip the wrapping
            res.extend([line[3:-1] for line in lines if line])
        return res[: min(limit, len(res))]

    def get_schema_result(self, show_data_path):
        # schema is a list of {'name': blah, 'type': blah, 'nullable': blah)
        # returns a None if nothing read from file
        res = None
        file_paths = notebook_hdfs_client.list_files(
            show_data_path + "/meta/schema.json"
        )
        if file_paths:
            lines = notebook_hdfs_client.read_file(file_paths[0])
            res = json.loads(lines[0])
        return res

    def _stop_job(self, job_id):
        self.oceanus.stop_job(self.OceanusUFFConstants.TEST_PROJECT_ID, job_id)
        completed, status = self.poll_job_status(
            job_id,
            target_statuses=[
                self.JobStatus.FAILED,
                self.JobStatus.CANCELLED,
                self.JobStatus.FINISHED,
                # do not add cancelling here, as the hdfs file may not be flushed soon enough
            ],
            interval=10,
            try_limit=36,
        )
        if not completed:
            # raise RuntimeError(
            #     'Cannot stop job properly, please stop the job on Oceanus manually, and retry.')
            display_msg("Oceanus任务停止超时，尝试读取运行结果中……", "WARN")

    def get_raw_df(
        self,
        pipeline: Pipeline,
        uid: str,
        limit: int = 100,
        options: dict = None,
        is_feature_group=False,
        is_sink_view=False,
    ) -> StreamDataFrame:
        pipeline.verify_state_id()
        if self.has_udf(pipeline):
            # register udfs to notebook, then register to Flink
            self.register_udfs_to_notebook(pipeline)
        options = dict() if options is None else options
        options["printFeatureGroup"] = "true" if is_feature_group else "false"
        options["printSinkView"] = "true" if is_sink_view else "false"
        running_timeout = int(options.get("stream_show_timeout") or 300)
        stream_sink_path = self.get_show_data_path(uid)
        job = self.create_or_update_job(
            pipeline=pipeline,
            stream_sink_path=stream_sink_path,
            limit=limit,
            options=options,
        )
        job_id = job["id"]
        self.start_or_restart_job(job_id)
        self.show_job_url(job_id)
        if (options.get("only_output_schema") or "false").lower() == "true":
            submitting, status = self.poll_job_status(
                job_id,
                target_statuses=[self.JobStatus.SUBMITTING],
                interval=1,
                try_limit=60,
            )
            if submitting:
                completed, status = self.poll_job_status(
                    # the job would fail because execute will not be called on scala side
                    # if only_output_schema is set to true
                    job_id,
                    target_statuses=[self.JobStatus.FAILED],
                    interval=2,
                    try_limit=running_timeout / 2,
                )
                if not completed:
                    print(
                        f"Stopping Oceanus job as timeout of {running_timeout}s reached, you can modify the timeout via stream_show_timeout in options"
                    )
                    self._stop_job(job_id)
                print("Retrieving output")
                try:
                    schema = self.get_schema_result(stream_sink_path)
                    return StreamDataFrame(schema=schema)
                except Exception as e:
                    display_msg(
                        f"未知异常，请进入Oceanus UI查看启动日志和Flink日志进行排查",
                        "WARN",
                    )
                    raise e
            else:
                raise RuntimeError(
                    "Cannot submit job properly, please stop the job on Oceanus manually, and retry"
                )
        else:
            started, status = self.poll_job_status(
                job_id, target_statuses=[self.JobStatus.RUNNING]
            )
            if started:
                print("Oceanus job started, waiting for its completion.")
                completed, status = self.poll_job_status(
                    job_id,
                    target_statuses=[
                        self.JobStatus.FAILED,
                        self.JobStatus.CANCELLED,
                        self.JobStatus.FINISHED,
                    ],
                    interval=10,
                    try_limit=running_timeout / 10,
                )
                if not completed:
                    print(
                        f"Stopping Oceanus job as timeout of {running_timeout}s reached, you can modify the timeout via stream_show_timeout in options"
                    )
                    self._stop_job(job_id)
                print("Retrieving output")
                try:
                    raw_rows = [
                        json.loads(r)
                        for r in self.get_show_result(
                            show_data_path=stream_sink_path, limit=limit
                        )
                    ]
                    if not raw_rows:
                        raise ValueError(
                            "Cannot assemble StreamDataFrame from empty result"
                        )
                    schema = self.get_schema_result(stream_sink_path)
                    return StreamDataFrame(raw_rows, schema)
                except Exception as e:
                    display_msg(
                        f"运行结果为空或有未知异常，如提高采样率不能解决，请进入Oceanus UI查看启动日志和Flink日志进行排查",
                        "WARN",
                    )
                    raise e
            else:
                raise RuntimeError(
                    "Cannot start job properly, please stop the job on Oceanus manually, and retry."
                )

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
        raw_df = self.get_raw_df(
            pipeline=pipeline,
            uid=uid,
            limit=limit,
            options=options,
            is_feature_group=is_feature_group,
            is_sink_view=is_sink_view,
        )
        return raw_df.show(limit=limit, vertical=vertical)

    def has_udf(self, pipeline: Pipeline):
        return len(pipeline.data.udfs) > 0

    def register_udfs_to_notebook(self, pipeline: Pipeline):
        # 用于在notebook直接调用用户的UDF，快速验证用户UDF代码。
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py") as tf:
            tf.write("from __future__ import annotations\n")
            tf.write("from typing import *")
            tf.write("\n")
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


class StreamField:

    def __init__(self, name: str, data_type: str, nullable: bool):
        self.name = name
        self.dataType = data_type
        self.nullable = nullable


class StreamSchema:

    def __init__(self, fields: list[StreamField]):
        self.fields = fields


class StreamDataFrame:

    def __init__(self, data=None, schema: list[dict] = None):
        self.data = data
        self._schema = schema

    @property
    def pandas_df(self):
        df = pd.DataFrame(self.data)
        return df if self._schema is None else df[[c["name"] for c in self._schema]]

    @property
    def schema(self):
        return StreamSchema(
            [
                StreamField(
                    name=col["name"], data_type=col["type"], nullable=col["nullable"]
                )
                for col in self._schema
            ]
        )

    def show(self, limit: int = 20, vertical: bool = False):
        df = self.pandas_df.head(limit)
        if not vertical:
            from IPython.display import display

            # to make it behaves like a print
            display(DisplayFullDataFrame(df))
        else:
            record_idx = 0
            for _, row in df.iterrows():
                print(f"----record {record_idx} ----")
                max_column_length = -1
                for column, value in row.items():
                    max_column_length = max(max_column_length, len(column.__str__()))
                for column, value in row.items():
                    column_with_space = column.__str__().ljust(max_column_length)
                    print(f"{column_with_space}\t\t\t\t | {value}")
                record_idx += 1
