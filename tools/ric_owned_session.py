"""Stateful RIC lifecycle core, driven by an injected request/reply transport.

No socket, vehicle endpoint or drawing graph is selected here. The transport
must honor the supplied timeout and return one complete correlated response.
This component prepares resource lifecycle testing, not visual proof.
"""
import hashlib
import struct
from ric_lifecycle import MAX_BODY, decode_body
from ric_resource_check import encode_distinct_create_body, encode_check_body, encode_profile_create_body
from ric_resource import encode_bitmap_body


class RicFailure(RuntimeError):
    pass


class OwnedSession:
    def __init__(self, exchange, identity, versions, client_id, timeout=1.0,
                 forbidden_handles=(200,), service_profile=False):
        if not callable(exchange):
            raise ValueError('Expected a bounded exchange transport')
        if type(client_id) is not int or not 1 <= client_id <= 65535:
            raise ValueError('Expected nonzero u16 client ID')
        if type(timeout) not in (int, float) or not 0 < timeout <= 5:
            raise ValueError('Timeout must be in (0, 5] seconds')
        self.create_body = (encode_profile_create_body(*identity, versions) if service_profile
                            else encode_distinct_create_body(identity, versions))
        self.exchange, self.client, self.timeout = exchange, client_id, timeout
        self.forbidden_handles = frozenset(forbidden_handles) | {0, 0xffffffff}
        self.handle, self.configuration_body = None, None
        self.next_request = 1
        self.state = 'new'
        self.resources = {}
        self.journal = []
        self.cleanup_report = None

    def _request(self, method, body):
        if not isinstance(body, bytes) or len(body) > MAX_BODY:
            raise ValueError('Invalid request body')
        if self.next_request > 65535:
            raise RicFailure('Request ID exhausted; no wrap or reconnect')
        request_id = self.next_request
        self.next_request += 1
        packet = struct.pack('>HHIHHBBBB', 0xb006, method, len(body)+8,
                             self.client, request_id, 1, 1, 0, 0) + body
        entry = dict(method=method, request_id=request_id,
                     body_sha256=hashlib.sha256(body).hexdigest(), outcome='pending')
        self.journal.append(entry)
        try:
            reply = self.exchange(packet, self.timeout)
            if not isinstance(reply, bytes) or not 16 <= len(reply) <= MAX_BODY+16:
                raise RicFailure('Invalid response size')
            svc, m, n, c, s, p, i, kind, code = struct.unpack('>HHIHHBBBB', reply[:16])
            if (svc,m,c,s,p,i) != (0xb006,method,self.client,request_id,1,1) or n != len(reply)-8:
                raise RicFailure('Uncorrelated or malformed response')
            if kind != 0x80 or code != 0:
                raise RicFailure('Server rejected request: kind=%d code=%d' % (kind,code))
            entry['outcome'] = 'protocol_acknowledged'
            return reply[16:]
        except Exception as error:
            entry['outcome'] = 'failed_or_uncertain'
            entry['error'] = str(error)
            raise

    def _empty(self, method, body):
        if self._request(method, body):
            raise RicFailure('Expected empty acknowledgement')

    def open(self):
        if self.state != 'new':
            raise RicFailure('Create is single-attempt; session cannot be reopened')
        self.state = 'create_pending'
        try:
            body = self._request(1, self.create_body)
            if len(body) < 4:
                raise RicFailure('Create reply lacks a handle')
            handle = struct.unpack_from('>I',body)[0]
            if handle in self.forbidden_handles:
                raise RicFailure('Create returned a reserved or known factory handle')
            # Save a correlated returned handle before parsing configuration so
            # a bad config can still trigger an explicit instance-release attempt.
            self.handle = handle
            self.configuration_body = body
            decoded = decode_body(1, 0x80, 0, body)
            self.state = 'created'
            return decoded
        except Exception:
            self.state = 'create_failed_or_uncertain'
            self.close()
            raise

    def _active(self):
        if self.state != 'created' or self.handle is None:
            raise RicFailure('A successful distinct create is required')

    def check(self, resource_id, resource_type):
        self._active()
        return self._check(resource_id, resource_type)

    def _check(self, resource_id, resource_type):
        body = self._request(2, encode_check_body(self.handle, resource_id, resource_type))
        if body not in (b'\0', b'\1'):
            raise RicFailure('Resource check lacks a Boolean result')
        return body == b'\1'

    def upload_bitmap(self, resource_id, resource_type, pair, image):
        """Resource-only trial, not a visible marker or ownership assertion.

        The caller must first establish the returned configuration's resource
        semantics; this core cannot manufacture that missing contract.
        """
        self._active()
        if resource_id in self.resources:
            raise RicFailure('Do not reuse a tracked resource ID')
        body = encode_bitmap_body(self.handle, resource_id, resource_type, pair, image)
        if self._check(resource_id, resource_type):
            raise RicFailure('Resource already reported present; refusing overwrite')
        # Record intent before send: a lost upload reply does not mean no upload.
        self.resources[resource_id] = resource_type
        try:
            self._empty(3, body)
            if not self._check(resource_id, resource_type):
                raise RicFailure('Resource not reported present after upload')
        except Exception:
            self.state = 'resource_failed_or_uncertain'
            self.close()
            raise

    def close(self):
        if self.cleanup_report is not None:
            return self.cleanup_report
        report = dict(resources=[], instance_dispose_acknowledged=False,
                      create_result_unknown=self.handle is None and self.state != 'new',
                      remote_image_erased=False, visual_test_passed=False)
        self.cleanup_report = report
        if self.handle is not None:
            for resource_id, resource_type in self.resources.items():
                row = dict(resource_id=resource_id, dispose_acknowledged=False,
                           post_dispose_check=None, errors=[])
                report['resources'].append(row)
                try:
                    self._empty(8, struct.pack('>II',self.handle,resource_id))
                    row['dispose_acknowledged'] = True
                except Exception as error:
                    row['errors'].append(str(error))
                # A failed disposal does not suppress the independent check.
                try:
                    row['post_dispose_check'] = self._check(resource_id,resource_type)
                except Exception as error:
                    row['errors'].append(str(error))
            try:
                self._empty(7,struct.pack('>I',self.handle))
                report['instance_dispose_acknowledged'] = True
            except Exception as error:
                report['instance_error'] = str(error)
        self.state = 'closed'
        return report

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, kind, value, traceback):
        self.close()
        return False
