from calendar import c
import json
import traceback
import uuid
import logging
from collections import defaultdict
from datetime import datetime, timedelta

# Only do basicConfig if no handlers have been configured
if len(logging._handlerList) == 0:
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
LOGGER = logging.getLogger(__name__)


# copied from mongoqueue
class Job(object):
    """
    This class is also used to represent jobs to the outside
    """
    def __init__(self, data, queue):
        self._data = data
        self._queue = queue
        # All currently known remote jobs as implemented in the Worker, redundantly organized by various aspects
        self.method_types = {
            "matching": [
                "getMatchesForSample",
                "getMatchesForSampleVs",
                "combineMatchesToCross",
            ],
            "query": [
                "getMatchesForUnmappedBinary",
                "getMatchesForMappedBinary",
                "getMatchesForSmdaReport",
            ],
            "blocks": [
                "getUniqueBlocks",
            ],
            "minhashing": [
                "updateMinHashesForSample",
                "updateMinHashes",
                "rebuildIndex",
            ],
            "collection": [
                "addBinarySample",
                "deleteSample",
                "modifySample",
                "deleteFamily",
                "modifyFamily",
            ],
            "sample_id": [
                "getMatchesForSampleVs",
                "getMatchesForSample",
                "updateMinHashesForSample",
                "deleteSample",
                "modifySample",
            ],
            "family_id": [
                "deleteFamily",
                "modifyFamily",
            ],
            "all": [
                "getMatchesForSample",
                "getMatchesForSampleVs",
                "combineMatchesToCross",
                "getMatchesForUnmappedBinary",
                "getMatchesForMappedBinary",
                "getMatchesForSmdaReport",
                "getUniqueBlocks",
                "updateMinHashesForSample",
                "updateMinHashes",
                "addBinarySample",
                "modifySample",
                "deleteSample",
                "modifyFamily",
                "deleteFamily",
                "rebuildIndex",
            ]
        }

    def __str__(self) -> str:
        return f"ID: {self.job_id} - {self.parameters} | created: {self.created_at}, finished: {self.finished_at}, result: {self.result}, progress: {self.progress}"
    
    @property
    def family(self) -> str:
        if self.method in ["addBinarySample"]:
            descriptor = json.loads(self._data["payload"]["descriptor"])
            return descriptor[1]["2"]

    @property
    def sha256(self) -> str:
        if self.method in ["getMatchesForUnmappedBinary", "getMatchesForMappedBinary", "getMatchesForSmdaReport", "addBinarySample"]:
            descriptor = json.loads(self._data["payload"]["descriptor"])
            return descriptor[2]["0"]
        
    @property
    def filename(self) -> str:
        if self.method in ["addBinarySample"]:
            descriptor = json.loads(self._data["payload"]["descriptor"])
            return descriptor[1]["1"]
    
    @property
    def family_id(self):
        if self.method in self.method_types["family_id"]:
            return int(self.arguments[0])
        if self.method == "getUniqueBlocks":
            if len(self.arguments) > 1:
                return int(self.arguments[1])

    @property
    def has_family_id(self):
        if self.method in self.method_types["family_id"] or self.method == "getUniqueBlocks":
            return True
        return False
    
    @property
    def sample_ids(self):
        sample_ids = []
        if self.method == "combineMatchesToCross":
            sample_ids = [int(key) for key, value in self.arguments[0].items()]
        elif self.method == "getUniqueBlocks":
            sample_ids = [int(sid) for sid in self.arguments[0]]
        elif self.method in self.method_types["sample_id"]:
            sample_ids.append(int(self.arguments[0]))
            if self.method == "getMatchesForSampleVs":
                sample_ids.append(int(self.arguments[1]))
        elif self.sample_id is not None:
            sample_ids.append(self.sample_id)
        return set(list(sample_ids))

    @property
    def sample_id(self):
        if self.method in self.method_types["sample_id"]:
            return int(self.arguments[0])
        elif self.method == "updateMinHashesForSample":
            return int(self.arguments[0])
        elif self.method == "getUniqueBlocks":
            if len(self.arguments[0]) > 0:
                return int(self.arguments[0][0])
        elif self.method == "deleteSample":
            return int(self.arguments[0])
        elif self.method == "modifySample":
            return int(self.arguments[0])

    @property
    def other_sample_id(self):
        if self.method == "getMatchesForSampleVs":
            return int(self.arguments[1])

    def has_sample_id(self, sample_id:int):
        if self.method in self.method_types["sample_id"]:
            if self.method == "getMatchesForSampleVs":
                return int(self.arguments[0]) == sample_id or int(self.arguments[1]) == sample_id
            else:
                return int(self.arguments[0]) == sample_id

    @property
    def is_matching_job(self):
        if self.method in self.method_types["matching"]:
            return True
        return False
    
    @property
    def is_minhashing_job(self):
        if self.method in self.method_types["minhashing"]:
            return True
        return False

    @property
    def is_query_job(self):
        if self.method in self.method_types["query"]:
            return True
        return False
    
    @property
    def is_block_job(self):
        if self.method in self.method_types["blocks"]:
            return True
        return False

    @property
    def is_collection_job(self):
        if self.method in self.method_types["collection"]:
            return True
        return False

    @property
    def method(self):
        if "payload" in self._data and "method" in self._data["payload"]:
            return self._data["payload"]["method"]

    @property
    def payload(self):
        return self._data["payload"]

    @property
    def arguments(self):
        combined_values = []
        if "payload" in self._data and "params" in self._data["payload"] and "method" in self._data["payload"]:
            payload_params = json.loads(self._data["payload"]["params"])
            indexed_key_values = []
            named_key_values = []
            for k, v in payload_params.items():
                try:
                    int(k)
                    indexed_key_values.append(v)
                except:
                    named_key_values.append(v)
            combined_values = indexed_key_values + named_key_values
        return combined_values

    @property
    def parameters(self):
        method_str = ""
        if "payload" in self._data and "params" in self._data["payload"] and "method" in self._data["payload"]:
            method_str = self._data["payload"]["method"]
            method_str += "(" + ", ".join([str(v) for v in self.arguments]) + ")"
        return method_str

    @property
    def all_dependencies(self):
        return self._data["all_dependencies"]

    @property
    def job_id(self):
        if isinstance(self._data["_id"], dict):
            return str(self._data["_id"]["$oid"])
        return self._data["_id"]

    @property
    def number(self):
        return self._data["number"] if "number" in self._data else -1

    @property
    def priority(self):
        return self._data["priority"]

    @property
    def attempts_left(self):
        return self._data["attempts_left"]

    @property
    def is_failed(self):
        return self._data["attempts_left"] == 0

    @property
    def locked_by(self):
        return self._data["locked_by"]

    @property
    def locked_at(self):
        if isinstance(self._data["locked_at"], dict):
            return str(self._data["locked_at"]["$date"])
        return self._data["locked_at"]

    @property
    def last_error(self):
        return self._data["last_error"]

    @property
    def finished_at(self):
        if isinstance(self._data["finished_at"], dict):
            return str(self._data["finished_at"]["$date"])
        return self._data["finished_at"]

    @property
    def is_finished(self):
        return self._data["finished_at"] is not None

    @property
    def duration(self):
        if self.is_finished:
            FMT = '%Y-%m-%d-%H:%M:%S'
            finished_at = self.finished_at[:10] + "-" + self.finished_at[11:19]
            started_at = self.started_at[:10] + "-" + self.started_at[11:19]
            duration = datetime.strptime(finished_at, FMT)-datetime.strptime(started_at, FMT)
            return duration
        return None

    @property
    def created_at(self):
        if isinstance(self._data["created_at"], dict):
            return str(self._data["created_at"]["$date"])
        return self._data["created_at"]

    @property
    def started_at(self):
        if isinstance(self._data["started_at"], dict):
            return str(self._data["started_at"]["$date"])
        return self._data["started_at"]

    @property
    def is_terminated(self):
        return self._is_terminated()

    @property
    def progress(self):
        return self._data["progress"] if "progress" in self._data else 0

    # NOTE: This is a GridFS id, not the actual result
    @property
    def result(self):
        return self._data["result"]

    @result.setter
    def result(self, res):
        self._data["result"] = res

    ## job control

    def complete(self, result=None):
        """job has been completed."""
        if result:
            self._data["result"] = result
        self._data["finished_at"] = datetime.now()
        self._data["progress"] = 1
        return self

    def error(self, message=None):
        """note an error processing a job, and return it to the queue."""
        self._data["locked_by"] = None
        self._data["locked_at"] = None
        self._data["last_error"] = message
        self._data["attempts_left"] -= 1

    def progressor(self, count=0):
        self._data["progress"] = count

    def __enter__(self):
        return self._data

    def __exit__(self, type, value, tb):
        if (type, value, tb) == (None, None, None):
            self.complete()
        else:
            error = traceback.format_exc()
            self.error(error)

    # only works for jobs that report progress
    # used_cached flag is useless for this kind of queue
    def _is_terminated(self, use_cached=False):
        terminated = self._data["terminated"]
        if terminated is None:
            return False
        return terminated

    # only works for jobs that report progress
    def terminate(self):
        self._data["terminated"] = True


class LocalQueue(object):
    def __init__(self):
        self._setup_empty_queue()
        self._worker = None
        self._job_counter = 0
        self.clean_interval = 10 ** 9
        self.cache_time = 10 ** 9
        self.max_attempts = 1

    def _setup_empty_queue(self):
        self._jobs = defaultdict(lambda: None)
        self._files = defaultdict(lambda: None)
        self._files_meta = defaultdict(lambda: None)
        self._descriptor_to_job = defaultdict(lambda: None)
        self._hash_to_file = defaultdict(lambda: None)

    def registerWorker(self):
        # left empty, as we only have one worker in local mode
        pass

    def unregisterWorker(self):
        # left empty, as we only have one worker in local mode
        pass

    def getQueueStatistics(self):
        # we don't track stats for the volatile local mode
        return {}

    def set_worker(self, worker):
        self._worker = worker

    def get_job(self, job_id):
        data = self._jobs[job_id]
        return data and Job(data, self)

    def get_jobs(self, start_index: int, limit: int, method=None, state=None, filter=None, ascencing=False):
        # TODO implement all the filtering methods properly
        jobs = []
        for job_id, job_document in self._jobs.items():
            if method is not None and job_document["payload"]["method"] != method:
                continue
            jobs.append(Job(job_document, self))
        return jobs[start_index:start_index+limit]

    def get_cached_job_id(self, payload):
        return self._descriptor_to_job[payload["descriptor"]]

    def _file_to_grid(self, file, metadata=None):
        id = str(uuid.uuid4())
        try:
            file.seek(0)
            data = file.read()
        except AttributeError:
            if not isinstance(file, (str, bytes)):
                raise TypeError("Only strings, bytes or file-like objecs are supported")
            if isinstance(file, str):
                try:
                    data = data.encode(self.encoding)
                except AttributeError:
                    raise TypeError("no encoding was specified")
            else:
                data = file
        self._files[id] = data
        self._files_meta[id] = metadata
        try:
            self._hash_to_file[metadata["sha256"]] = id
        except:
            pass
        return id

    def _grid_to_file(self, grid, results_only=True):
        file = self._files[grid]
        if file is None:
            return None
        if results_only:
            metadata = self._files_meta[grid]
            if not "result" in metadata or not metadata["result"]:
                return b'"Access Not Allowed"'
        return file

    def get_file_by_hash_inc_lock(self, sha256):
        id = self._hash_to_file[sha256]
        self._inc_lock(id)
        return id

    def _get_file_by_hash(self, sha256):
        return self._hash_to_file[sha256]

    def _inc_lock(self, id):
        if id is None:
            return
        try:
            self._files_meta[id]["tmp_lock"] += 1
        except:
            pass

    def _dec_lock(self, id):
        if id is None:
            return
        try:
            self._files_meta[id]["tmp_lock"] -= 1
        except:
            pass

    def add_job_id_to_file(self, job_id, file_id):
        self._files_meta[file_id]["jobs"].append(job_id)
        self._dec_lock(file_id)

    def _dicts_to_grid(self, dicts, **kwargs):
        return self._file_to_grid(json.dumps(dicts).encode("ascii"), **kwargs)

    def _grid_to_dicts(self, grid, **kwargs):
        return json.loads(self._grid_to_file(grid, **kwargs).decode("ascii"))

    def _grid_to_meta(self, grid):
        return self._files_meta[grid]

    def _delete_grid(self, grid):
        meta = self._files_meta[grid]
        try:
            if self._hash_to_file[meta["sha256"]] == grid:
                del self._hash_to_file[meta["sha256"]]
        except:
            pass
        del self._files[grid]
        del self._files_meta[grid]

    def put(self, payload, await_jobs=[]):
        id = str(uuid.uuid4())
        job_data = defaultdict(lambda: None)
        job_data["_id"] = id
        job_data["number"] = self._job_counter
        self._job_counter += 1
        job_data["payload"] = payload
        job_data["unfinished_dependencies"] = await_jobs
        job_data["all_dependencies"] = await_jobs
        job_data["attempts_left"] = self.max_attempts
        job_data["created_at"] = datetime.now()
        self._jobs[id] = job_data
        self._descriptor_to_job[payload["descriptor"]] = id
        job_data["started_at"] = datetime.now()
        # NOTE: we can just ignore await jobs, because all jobs are
        #       executed in submission order
        self._worker._executeJob(Job(job_data, self))
        return id

    def clear(self):
        self.terminate_all_jobs()
        self._setup_empty_queue()

    def delete_job(self, id):
        if id not in self._jobs:
            return 0
        job = self._jobs[id]
        result = job["result"]
        file_params = json.loads(job["payload"]["file_params"])
        descriptor = job["payload"]["descriptor"]
        if self._descriptor_to_job[descriptor] == id:
            del self._descriptor_to_job[descriptor]
        del self._jobs[id]
        self._delete_grid(result)
        for f in file_params.values():
            meta = self._grid_to_meta(f)
            LOGGER.debug("Job meta: %s", meta)
            meta["jobs"].remove(id)
        return 1
    delete_history = []

    def delete_jobs(self, method=None, created_before=None, finished_before=None):
        delete_list = []
        deleted_count = 0
        for d in self._jobs.values():
            if d["payload"]["method"] is not None and d["payload"]["method"] != method:
                continue
            if d["created_at"] is not None and d["created_at"] >= finished_before:
                continue
            if d["finished_at"] is not None and d["finished_at"] >= finished_before:
                continue
            delete_list.append(d["_id"])
        for id in delete_list:
            deleted_count += self.delete_job(id)
        return deleted_count

    def clean(self):
        time_threshold = datetime.now() - timedelta(seconds=self.cache_time)
        delete_list = []
        for d in self._jobs.values():
            if (d["finished_at"] is not None) and d["finished_at"] < time_threshold:
                delete_list.append(d["_id"])

        self.delete_history.append(delete_list)
        LOGGER.debug("Perfomed clean, delete_history now has %d entries.", len(self.delete_history))

        for id in delete_list:
            self.delete_job(id)

        delete_list = []
        for id, meta in self._files_meta.items():
            if "result" in meta and meta["result"]:
                continue
            if len(meta["jobs"]) == 0 and meta["tmp_lock"] == 0:
                delete_list.append(id)
        for id in delete_list:
            self._delete_grid(id)

    def terminate_all_jobs(self):
        for job in self._jobs.values():
            if job["result"] is None:
                job["terminated"] = True

    def next(self):
        # this is a dummy, as we don't have an actual queue
        return None