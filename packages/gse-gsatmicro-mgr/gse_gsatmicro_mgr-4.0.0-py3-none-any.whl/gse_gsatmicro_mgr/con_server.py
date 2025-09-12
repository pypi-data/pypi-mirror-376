# Command line interface server implementation (stdin for requests, stdout for results)
# Allows accessing gsemgr with an HTTP API

# GSE Proprietary Software License
# Copyright (c) 2025 Global Satellite Engineering, LLC. All rights reserved.
# This software and associated documentation files (the "Software") are the proprietary and confidential information of Global Satellite Engineering, LLC ("GSE"). The Software is provided solely for the purpose of operating applications distributed by GSE and is subject to the following conditions:

# 1. NO RIGHTS GRANTED: This license does not grant any rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell the Software.
# 2. RESTRICTED ACCESS: You may only access the Software as part of a GSE application package and only to the extent necessary for operation of that application package.
# 3. PROHIBITION ON REVERSE ENGINEERING: You may not reverse engineer, decompile, disassemble, or attempt to derive the source code of the Software.
# 4. PROPRIETARY NOTICES: You must retain all copyright, patent, trademark, and attribution notices present in the Software.
# 5. NO WARRANTIES: The Software is provided "AS IS", without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement.
# 6. LIMITATION OF LIABILITY: In no event shall GSE be liable for any claim, damages or other liability, whether in an action of contract, tort or otherwise, arising from, out of or in connection with the Software or the use or other dealings in the Software.
# 7. TERMINATION: This license will terminate automatically if you fail to comply with any of the terms and conditions of this license. Upon termination, you must destroy all copies of the Software in your possession.

# THE SOFTWARE IS PROTECTED BY UNITED STATES COPYRIGHT LAW AND INTERNATIONAL TREATY. UNAUTHORIZED REPRODUCTION OR DISTRIBUTION IS SUBJECT TO CIVIL AND CRIMINAL PENALTIES.

from . import vfs
from . import common
from gse_gsatmicro_utils import utils
import json
import sys
import base64
import threading
import queue

#######################################################################################################################
# Local function and data

# httpd logger
logger = utils.Logger("cond")
# Request queue
req_q = queue.Queue()
# stdout/stderr lock
con_lock = threading.Lock()

# Mapping between the acstion in a request and the correponding handler
act_map = {
    "fs_list": common.fs_list,
    "fs_stat": common.fs_stat,
    "fs_kind": common.fs_kind,
    "fs_get": lambda fs, req, logger: base64.b64encode(common.fs_get(fs, req, logger)).decode("ascii"),
    "fs_create": common.fs_create,
    "fs_remove": common.fs_remove,
    "fs_put": lambda fs, req, logger: common.fs_put(fs, req, logger, b64=True),
    "version": common.cmd_version,
    "reset": common.cmd_reset,
    "run": common.cmd_run_code
}

# Send an "invalid request" response
def invalid(req_id, data="invalid request"):
    con_lock.acquire()
    try:
        sys.stdout.write(json.dumps({"id": req_id, "err": data}))
        sys.stdout.write("\r\n")
        sys.stdout.flush()
    finally:
        con_lock.release()

# Call the given function with the given arguments
# If an exception is raised, catch it and return an invalid request rerpose
def req_wrap(req_id, f, *args, **kwargs):
    try:
        if (res := f(*args, **kwargs)) == None:
            res = True
        res = {"id": req_id, "res": res}
    except Exception as e:
        res = {"id": req_id, "err": str(e)}
    return json.dumps(res)

# Console thread: read a line from stdin and save it to the request queue
def stdin_read_thread(q):
    while True:
        try:
            q.put(input(""))
        except (EOFError, KeyboardInterrupt):
            q.put(None)
            break

# Return a request dictionary that is suitable to use for the function in common.py
# In this case, this means that the "act" and "id" keys should be removed, since they are specific to the con server
def fix_req(r):
    return {k: v for k, v in r.items() if not k in ("act", "id")}

#######################################################################################################################
# Commands

# 'cond' command handler
def cmd_cond(ser, args):
    # Redirect all logs to stderr
    utils.all_logs_to_stderr(True)
    # Synchronize all stdout/stderr writes
    utils.set_logs_con_lock(con_lock)
    # Get filesystem instance
    fs = vfs.get_vfs()
    # Start console read thread
    threading.Thread(target=stdin_read_thread, args=(req_q, ), daemon=True).start()
    # The server loop runs here
    logger.info("Starting console server")
    while True:
        try:
            if (req := req_q.get()) == None:
                break
            # Read a single request which should be valud JSON
            try:
                req = json.loads(req)
            except:
                logger.warning(f"Received invalid reqeust")
                invalid(-1)
                continue
            # The request should have an "act" key (action)
            if (not isinstance(req, dict)) or (not "act" in req) or (not "id" in req):
                logger.warning("Required key(s) 'act' and/or 'id' not found in request")
                invalid(-1)
                continue
            # Check action
            if (act := req["act"]) == "exit": # server must terminate
                break
            elif not act in act_map: # unknown action
                logger.warning(f"Unknown action {act} in request")
                invalid(req["id"])
                continue
            else: # action found, execute its handler
                res = req_wrap(req["id"], act_map[act], fs, fix_req(req), logger)
                con_lock.acquire()
                try:
                    sys.stdout.write(res)
                    sys.stdout.write("\r\n")
                    sys.stdout.flush()
                finally:
                    con_lock.release()
        except KeyboardInterrupt:
            break
    logger.info("Server exited")