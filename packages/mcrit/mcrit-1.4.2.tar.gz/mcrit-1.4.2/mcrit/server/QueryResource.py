import re
import logging

import falcon

from mcrit.server.utils import timing, jsonify, getMatchingParams
from mcrit.index.MinHashIndex import MinHashIndex
from mcrit.server.utils import db_log_msg

class QueryResource:
    def __init__(self, index: MinHashIndex):
        self.index = index
        self._query_option_best_only = False

    @timing
    def on_post_query_smda(self, req, resp):
        parameters = getMatchingParams(req.params)
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_post_query_smda - failed - no POST body.")
            return
        smda_report = req.media
        summary = self.index.getMatchesForSmdaReport(smda_report, **parameters)
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_post_query_smda - success.")

    @timing
    def on_post_query_binary(self, req, resp):
        parameters = getMatchingParams(req.params)
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_post_query_binary - failed - no POST body.")
            return
        binary = req.stream.read()
        summary = self.index.getMatchesForUnmappedBinary(binary, **parameters)
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_post_query_binary - success.")

    @timing
    def on_post_query_binary_mapped(self, req, resp, base_address=None):
        parameters = getMatchingParams(req.params)
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_post_query_binary_mapped - failed - no POST body.")
            return
        # convert string to int. 0 means figure out base automatically.
        base_address = int(base_address, 0)
        binary = req.stream.read()
        summary = self.index.getMatchesForMappedBinary(binary, base_address, **parameters)
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_post_query_binary_mapped - success.")

    @timing
    def on_post_query_smda_function(self, req, resp):
        parameters = getMatchingParams(req.params)
        if not req.content_length:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "POST request without body can't be processed."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_post_query_smda_function - failed - no POST body.")
            return
        smda_function = req.media
        summary = self.index.getMatchesForSmdaFunction(smda_function, **parameters)
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_post_query_smda_function - success.")

    @timing
    def on_get_query_pichash(self, req, resp, pichash):
        pichash_pattern = "[a-fA-F0-9]{16}"
        match = re.match(pichash_pattern, pichash)
        if not match:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "No valid PicHash provided."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_get_query_pichash - failed - no valid PicHash.")
            return
        pichash_int = int(pichash, 16)
        pichash_matches = self.index.getMatchesForPicHash(pichash_int)
        resp.data = jsonify({"status": "successful", "data": pichash_matches})
        db_log_msg(self.index, req, f"QueryResource.on_get_query_pichash - success.")

    @timing
    def on_get_query_pichash_summary(self, req, resp, pichash):
        pichash_pattern = "[a-fA-F0-9]{16}"
        match = re.match(pichash_pattern, pichash)
        if not match:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "No valid PicHash provided."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_get_query_pichash_summary - failed - no valid PicHash.")
            return
        pichash_int = int(pichash, 16)
        pichash_matches = self.index.getMatchesForPicHash(pichash_int)
        summary = {
            "families": len(set([e[0] for e in pichash_matches])),
            "samples": len(set([e[1] for e in pichash_matches])),
            "functions": len(set([e[2] for e in pichash_matches])),
        }
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_get_query_pichash_summary - success.")

    @timing
    def on_get_query_picblockhash(self, req, resp, picblockhash):
        pichash_pattern = "[a-fA-F0-9]{16}"
        match = re.match(pichash_pattern, picblockhash)
        if not match:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "No valid PicHash provided."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_get_query_picblockhash - failed - no valid PicHash.")
            return
        pichash_int = int(picblockhash, 16)
        pichash_matches = self.index.getMatchesForPicBlockHash(pichash_int)
        resp.data = jsonify({"status": "successful", "data": pichash_matches})
        db_log_msg(self.index, req, f"QueryResource.on_get_query_picblockhash - success.")

    @timing
    def on_get_query_picblockhash_summary(self, req, resp, picblockhash):
        pichash_pattern = "[a-fA-F0-9]{16}"
        match = re.match(pichash_pattern, picblockhash)
        if not match:
            resp.data = jsonify(
                {
                    "status": "failed",
                    "data": {"message": "No valid PicHash provided."},
                }
            )
            resp.status = falcon.HTTP_400
            db_log_msg(self.index, req, f"QueryResource.on_get_query_picblockhash_summary - failed - no valid PicHash.")
            return
        pichash_int = int(picblockhash, 16)
        pichash_matches = self.index.getMatchesForPicBlockHash(pichash_int)
        summary = {
            "families": len(set([e[0] for e in pichash_matches])),
            "samples": len(set([e[1] for e in pichash_matches])),
            "functions": len(set([e[2] for e in pichash_matches])),
            "offsets" : len(pichash_matches)
        }
        resp.data = jsonify({"status": "successful", "data": summary})
        db_log_msg(self.index, req, f"QueryResource.on_get_query_picblockhash_summary - success.")
