#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: concurrency.py
# Author: Yuxin Wu <ppwwyyxx@gmail.com>

import threading
from contextlib import contextmanager
from itertools import izip
import tensorflow as tf

from .utils import expand_dim_if_necessary
from .naming import *
import logger

class StoppableThread(threading.Thread):
    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()


class EnqueueThread(threading.Thread):
    def __init__(self, sess, coord, enqueue_op, dataflow, queue):
        super(EnqueueThread, self).__init__()
        self.sess = sess
        self.coord = coord
        self.input_vars = sess.graph.get_collection(INPUT_VARS_KEY)
        self.dataflow = dataflow
        self.op = enqueue_op
        self.queue = queue

        self.daemon = True

    def run(self):
        try:
            while True:
                for dp in self.dataflow.get_data():
                    if self.coord.should_stop():
                        return
                    feed = dict(izip(self.input_vars, dp))
                    self.sess.run([self.op], feed_dict=feed)
                #print '\nExauhsted!!!'
        except tf.errors.CancelledError as e:
            pass
        except Exception:
            logger.exception("Exception in EnqueueThread:")
            self.queue.close(cancel_pending_enqueues=True)
            self.coord.request_stop()