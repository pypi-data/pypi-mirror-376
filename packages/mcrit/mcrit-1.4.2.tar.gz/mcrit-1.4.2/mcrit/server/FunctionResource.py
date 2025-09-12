import logging
import re

import falcon

from mcrit.server.utils import timing, jsonify
from mcrit.index.MinHashIndex import MinHashIndex
from mcrit.server.utils import db_log_msg


class FunctionResource:
    def __init__(self, index: MinHashIndex):
        self.index = index

    @timing
    def on_get(self, req, resp, function_id=None):
        query_with_xcfg = False 
        if "with_xcfg" in req.params:
            query_with_xcfg = req.params["with_xcfg"].lower().strip() == "true"
        if not self.index.isFunctionId(function_id):
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "We don't have a function with that id."},
                }
            )
            resp.status = falcon.HTTP_404
            db_log_msg(self.index, req, f"FunctionResource.on_get - failed - {function_id} unknown.")
            return
        data = self.index.getFunctionById(function_id, with_xcfg=query_with_xcfg).toDict()
        resp.data = jsonify(
            {
                "status": "successful",
                "data": data,
            }
        )
        db_log_msg(self.index, req, f"FunctionResource.on_get - success - {function_id}.")

    @timing
    def on_post_collection(self, req, resp):
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"FunctionResource.on_post - failed - no POST body.")
            return
        with_label_only = False 
        if "with_label_only" in req.params:
            with_label_only = req.params["with_label_only"].lower().strip() == "true"
        # assume the POST body consists of comma separated function_ids
        post_body = req.stream.read()
        if re.match(b"^\d+(?:[\s]*,[\s]*\d+)*$", post_body):
            target_function_ids = [int(function_id) for function_id in post_body.split(b",")]
            function_entries = {}
            for function_id in target_function_ids:
                function_entry = self.index.getFunctionById(function_id, with_xcfg=False).toDict()
                if function_entry:
                    if with_label_only and not function_entry["function_labels"]:
                        continue
                    function_entries[function_id] = function_entry
            resp.data = jsonify({"status": "successful", "data": function_entries})
            resp.status = falcon.HTTP_200
            db_log_msg(self.index, req, f"FunctionResource.on_post - success.")
            return
        resp.status = falcon.HTTP_400
        db_log_msg(self.index, req, f"FunctionResource.on_post - failed - invalid body format.")

    @timing
    def on_get_collection(self, req, resp):
        # parse optional request parameters
        start_index = 0 
        if "start" in req.params:
            try:
                start_index = int(req.params["start"])
            except:
                pass
        limit_function_count = 0 
        if "limit" in req.params:
            try:
                limit_function_count = int(req.params["limit"])
            except:
                pass
        function_overview = {}
        function_entries = self.index.getFunctions(start_index, limit_function_count)
        for function_entry in function_entries:
            function_overview[function_entry.function_id] = function_entry.toDict()
        resp.data = jsonify({"status": "successful", "data": function_overview})
        db_log_msg(self.index, req, f"FunctionResource.on_get_collection - success.")
