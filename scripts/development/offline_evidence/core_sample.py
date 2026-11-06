"""Pure composition of one retained public Core run, never project authority.

The caller supplies captured bytes and the existing passive OTS module. No
paths from a record are followed, no controller code is executed, and no RPC,
network, process, authentication, or full-chain replay is performed here.
"""
import hashlib
import math

PREFIX = 'docs/development/mainline-execution-2026-10-19-pruned-core-sample-execution-rev-001/'
BOUND_FILES = {'result': 'online-107-RESULT.json', 'events': 'online-107-PUBLIC_EVENTS.jsonl',
               'controller': 'supervise_core.metadata-rescan.py', 'config': 'bitcoin.conf.cache512-continuation.txt'}
FIXED_HASH = '000000000000000000007f0753c6209263c7072e51b725e89e75a0c708b90345'
# Historical strings from the fixed D199 run, never paths to access/execute.
HISTORICAL_ROOT = '/Users/sage/Library/Application Support/ForecastProvenance/CoreResearch-Pruned-31.1'
LAUNCH_ARGV = [HISTORICAL_ROOT+'/software/bitcoin-31.1/bin/bitcoind',
               '-conf='+HISTORICAL_ROOT+'/data/bitcoin.conf',
               '-datadir='+HISTORICAL_ROOT+'/data', '-networkactive=1',
               '-printtoconsole=0', '-nodebuglogfile']
MEMORY_POLICY = {'id': 'D199_OWNER_APPROVED_FP2_RSS8_MARGIN64',
                 'footprint_upper_stop_bytes': 2080374784, 'rss_stop_bytes': 8522825728,
                 'sampling_is_not_atomic_quota': True}
RETRY_POLICY = {'maximum_attempts': 2, 'HTTP_timeout_only': True,
                'guarded_cooldown_target_seconds': 120, 'first_CLI_timeout_seconds': 5,
                'first_subprocess_timeout_seconds': 12, 'guarded_retry_CLI_timeout_seconds': 30,
                'guarded_retry_process_timeout_seconds': 37,
                'guarded_retry_resource_check_target_seconds': 5}
FIXED_DIGESTS = {
    'controller': '0b37b628c290bf34ac263ffe38a3d321c93e8217a3714b453561563809a8619f',
    'config': '01439530bd38ba5a74794a2a86ca63f3f0a22d60cf48a04092e33aa32fa1dd4b',
    'pdf': 'c70972a12908b73c2407d9cc6842ba2a02203a690f3090cd29f30c45f0cfd93d',
    'proof': '0a63adf8a7b47b68d42aec05f365f78a631e64f734b8af5bc594188ee2d751e9',
    'header': 'e32a7c960950bc80adefad2bd7fdfadc133441e1fd7f98346da7f5cee8d76185',
}


def _same_typed(actual, expected):
    """Exact finite JSON profile; bool/int and int/float are distinct."""
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(_same_typed(actual[k], v) for k, v in expected.items())
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(_same_typed(a, b) for a, b in zip(actual, expected))
    return actual == expected


def _finite_object(raw, ots):
    value = ots._service_json(raw)
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError('nonfinite JSON number')
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return value


def consume_core_sample(inputs, ots):
    result = {'status': 'MISSING', 'scope': 'D199_RETAINED_LOCAL_CORE_PUBLIC_GDP_SAMPLE_ONLY',
              'findings': [], 'subject_link': None, 'retained_live_resource_records': 0,
              'complete_consumer_observations': 0,
              'evidence_kind': 'PARSED_RPC_OBSERVATIONS_IN_ORIGINAL_CONTROLLER_RECORDS',
              'controller_exit_kind': 'RETAINED_LOCAL_OBSERVATION_NOT_REOBSERVED_OR_AUTHENTICATED',
              'compact_evidence_replays_full_chain': False,
              'PGP_publisher': 'NOT_INDEPENDENTLY_VERIFIED',
              'authenticated_time': 'NOT_ESTABLISHED', 'project_subject_binding': 'NOT_ESTABLISHED',
              'project_Strong': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
              'protocol_state_change': 'NONE'}
    findings = result['findings']

    def finding(item, error, status='REJECTED'):
        findings.append({'item': item, 'status': status, 'error': error})

    roles = {'result', 'events', 'verification', 'controller', 'config', 'pdf', 'proof', 'header'}
    if type(inputs) is not dict or set(inputs) != roles:
        finding('inputs', 'CORE_INPUT_ROLES_INVALID')
        result['status'] = 'REJECTED'
        return result
    raw = {}
    for name, value in inputs.items():
        if value is None:
            finding(name, 'CORE_INPUT_MISSING', 'MISSING')
        elif type(value) is not bytes or not 0 < len(value) <= (2**21 if name == 'pdf' else 2**20):
            finding(name, 'CORE_INPUT_BYTES_OR_LIMIT')
        else:
            raw[name] = value
            if name in FIXED_DIGESTS and hashlib.sha256(value).hexdigest() != FIXED_DIGESTS[name]:
                finding(name, 'CORE_FIXED_INPUT_IDENTITY_MISMATCH')
    docs = {}
    for name in ('result', 'verification'):
        if name in raw:
            try:
                docs[name] = _finite_object(raw[name], ots)
            except (ValueError, UnicodeError, RecursionError):
                finding(name, 'CORE_JSON_INVALID')
    events = None
    if 'events' in raw:
        try:
            lines = raw['events'].splitlines()
            if not raw['events'].endswith(b'\n') or not 1 <= len(lines) <= 4096:
                raise ValueError('framing')
            events = [_finite_object(line, ots) for line in lines]
        except (ValueError, UnicodeError, RecursionError):
            finding('events', 'CORE_EVENTS_JSON_INVALID')
    r, v = docs.get('result'), docs.get('verification')
    if v is not None:
        try:
            rows = v['identities']
            if (type(rows) is not list or len(rows) > 64
                    or any(type(x) is not dict or set(x) != {'path', 'bytes', 'sha256'} for x in rows)
                    or len({x['path'] for x in rows}) != len(rows)):
                raise ValueError('identity rows')
            for name, path in BOUND_FILES.items():
                row = next((x for x in rows if x['path'] == PREFIX+path), None)
                if row is None:
                    finding(name, 'CORE_INPUT_BINDING_MISSING', 'MISSING')
                elif name in raw and (type(row['bytes']) is not int or row['bytes'] != len(raw[name])
                        or row['sha256'] != hashlib.sha256(raw[name]).hexdigest()):
                    finding(name, 'CORE_INPUT_BINDING_MISMATCH')
            if (type(v['controller_exit_code']) is not int or v['controller_exit_code'] != 0
                    or v['segment'] != 107 or type(v['segment']) is not int):
                raise ValueError('controller exit or segment')
            if (v.get('exception_type') is not None
                    or any(v.get(k) is not True for k in ('sample_chain_verified',
                    'all_retained_live_resources_within_bounds', 'final_disk_within_bounds'))
                    or any(v.get(k) != [] for k in ('failed_consumers', 'missing_consumer_results',
                                                    'matched_restore_floor_violations'))):
                finding('verification', 'CORE_VERIFICATION_NEGATIVE')
            if type(v.get('observed_height_floor')) is not int or v['observed_height_floor'] != 972170:
                finding('verification', 'CORE_RESTORE_FLOOR_INVALID')
            if v.get('missing_retry_results_not_counted_as_success') != 0:
                finding('verification', 'RETAINED_RETRY_RESULT_MISSING', 'MISSING')
        except (ValueError, TypeError, KeyError):
            finding('verification', 'CORE_VERIFICATION_INVALID')
    if r is not None:
        for field, expected, code in (
                ('argv', LAUNCH_ARGV, 'CORE_LAUNCH_PROFILE_MISMATCH'),
                ('memory_policy', MEMORY_POLICY, 'CORE_MEMORY_POLICY_MISMATCH'),
                ('read_retry_policy', RETRY_POLICY, 'CORE_RETRY_POLICY_MISMATCH')):
            if not _same_typed(r.get(field), expected):
                finding('result:'+field, code)
        try:
            chain, header = r['last_chain']['result'], r['sample_header_verbose']['result']
            raw_header = bytes.fromhex(r['sample_header_raw']['result'])
            integer = lambda x: type(x) is int
            if (r['mode'] != 'online' or type(r['segment']) is not int or r['segment'] != 107
                    or not integer(r['pid']) or r['pid'] <= 0 or r['protocol_state_change'] != 'NONE'
                    or r['sample_chain_verified'] is not True
                    or r['status'] != 'PUBLIC_SAMPLE_CORE_OBSERVATION_MATCHED_NOT_PROJECT_STRONG'
                    or r['last_chain']['ok'] is not True or chain['chain'] != 'main'
                    or not integer(chain['blocks']) or not integer(chain['headers'])
                    or chain['headers'] < chain['blocks'] or chain['blocks'] < 912095
                    or chain['initialblockdownload'] is not False or chain['pruned'] is not True
                    or r['sample_hash'] != {'ok': True, 'result': FIXED_HASH}
                    or r['sample_header_raw']['ok'] is not True or r['sample_header_verbose']['ok'] is not True
                    or len(raw_header) != 80
                    or hashlib.sha256(hashlib.sha256(raw_header).digest()).digest()[::-1].hex() != FIXED_HASH
                    or header['hash'] != FIXED_HASH or not integer(header['height']) or header['height'] != 912095
                    or not integer(header['confirmations']) or header['confirmations'] != chain['blocks']-912095+1):
                raise ValueError('sample')
            comparisons = {'version': int.from_bytes(raw_header[:4], 'little', signed=True),
                           'versionHex': format(int.from_bytes(raw_header[:4], 'little'), '08x'),
                           'previousblockhash': raw_header[4:36][::-1].hex(),
                           'merkleroot': raw_header[36:68][::-1].hex(),
                           'time': int.from_bytes(raw_header[68:72], 'little'),
                           'bits': format(int.from_bytes(raw_header[72:76], 'little'), '08x'),
                           'nonce': int.from_bytes(raw_header[76:80], 'little')}
            if any(type(header[k]) is not type(value) or header[k] != value for k, value in comparisons.items()):
                raise ValueError('verbose')
            if 'header' in raw and r['sample_header_raw']['result'].encode('ascii') != raw['header']:
                raise ValueError('retained header')
            shutdown = r['shutdown']
            if (shutdown['pid'] != r['pid'] or shutdown['confirmed_exited'] is not True
                    or type(shutdown['exit_code']) is not int or shutdown['exit_code'] != 0
                    or shutdown['stop_rpc']['ok'] is not True):
                raise ValueError('shutdown')
            if v is not None and (v['shutdown'] != shutdown or v['status'] != r['status']):
                raise ValueError('verification mismatch')
            result.update(observed_blocks=chain['blocks'], observed_headers=chain['headers'],
                          observed_IBD=False, sample_height=912095, sample_hash=FIXED_HASH,
                          confirmations_observed=header['confirmations'])
        except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
            finding('result', 'CORE_SAMPLE_FIELDS_INVALID')
        try:
            final = r['final_resources']
            if (any(type(final[k]) is not int for k in ('logical_bytes', 'allocated_bytes', 'free_bytes'))
                    or min(final['logical_bytes'], final['allocated_bytes']) < 0
                    or max(final['logical_bytes'], final['allocated_bytes']) >= 31675383808
                    or final['free_bytes'] <= 32749125632):
                raise ValueError('final disk')
        except (ValueError, TypeError, KeyError):
            finding('result', 'CORE_FINAL_RESOURCE_INVALID')
        if v is not None and any(v.get(k) != r.get('last_chain') for k in (
                'last_retained_successful_chain_read', 'last_successful_full_observation_chain_from_result')):
            finding('verification', 'CORE_VERIFICATION_CHAIN_MISMATCH')
    if events is not None:
        try:
            if (events[0]['stage'] != 'SPAWNED' or events[-1]['stage'] != 'SEGMENT_RESULT'
                    or sum(e.get('stage') == 'SPAWNED' for e in events) != 1
                    or sum(e.get('stage') == 'SEGMENT_RESULT' for e in events) != 1
                    or events[0]['mode'] != 'online'
                    or (r is not None and (events[0]['pid'] != r['pid'] or
                        {k: x for k, x in events[-1].items() if k not in ('stage', 'observed_at_utc')} != r))):
                raise ValueError('framing')
        except (ValueError, TypeError, KeyError):
            finding('events', 'CORE_EVENT_FRAMING_INVALID')
        last_sync = None
        timeout_events = sum(e.get('stage') == 'READ_RPC_HTTP_TIMEOUT' for e in events)
        retry_successes = 0
        for index, event in enumerate(events):
            if event.get('stage') == 'SYNC_OBSERVATION':
                last_sync = event
                complete = True
                for name in ('chain', 'network', 'peer_diagnostics'):
                    observation = event.get(name)
                    if type(observation) is not dict or type(observation.get('ok')) is not bool:
                        finding(str(index)+':'+name, 'RETAINED_CONSUMER_MISSING', 'MISSING'); complete = False
                    elif not observation['ok']:
                        finding(str(index)+':'+name, 'RETAINED_CONSUMER_FAILED'); complete = False
                    else:
                        retry_successes += observation.get('attempts') == 2
                        if name in ('network', 'peer_diagnostics'):
                            payload = observation.get('result')
                            if payload is None:
                                finding(str(index)+':'+name, 'RETAINED_CONSUMER_PAYLOAD_MISSING', 'MISSING')
                                complete = False
                            else:
                                try:
                                    if type(payload) is not dict:
                                        raise ValueError('payload')
                                    if name == 'network':
                                        if (payload['networkactive'] is not True or payload['localaddresses'] != []
                                                or type(payload['connections']) is not int or payload['connections'] < 0
                                                or type(payload['version']) is not int):
                                            raise ValueError('network')
                                    elif (payload['derived_diagnostic_only'] is not True
                                          or payload['raw_response_retained'] is not False
                                          or type(payload['peers']) is not list or len(payload['peers']) > 32
                                          or any(type(row) is not dict or type(row.get('row')) is not int
                                                 or type(row.get('missing_fields')) is not list
                                                 or type(row.get('invalid_fields')) is not list
                                                 for row in payload['peers'])):
                                        raise ValueError('peer diagnostics')
                                except (ValueError, TypeError, KeyError):
                                    finding(str(index)+':'+name, 'RETAINED_CONSUMER_PAYLOAD_INVALID')
                                    complete = False
                try:
                    chain = event['chain']['result']
                    if (chain['chain'] != 'main' or chain['pruned'] is not True
                            or type(chain['blocks']) is not int or chain['blocks'] < 972170
                            or type(chain['headers']) is not int or chain['headers'] < chain['blocks']
                            or type(chain['initialblockdownload']) is not bool):
                        raise ValueError('chain')
                except (ValueError, TypeError, KeyError):
                    finding(str(index)+':chain', 'RETAINED_CHAIN_INVALID')
                result['complete_consumer_observations'] += complete
            if event.get('stage') in ('SYNC_OBSERVATION', 'READ_RPC_SINGLE_RETRY_PREFLIGHT'):
                try:
                    x = event['resources']; memory = x['own_node_memory']
                    fields = ('logical_bytes', 'allocated_bytes', 'free_bytes', 'own_node_rss_bytes')
                    if (any(type(x[k]) is not int for k in fields) or memory['ok'] is not True
                            or type(memory['physical_footprint_upper_bytes']) is not int
                            or (r is not None and memory['pid'] != r['pid'])
                            or not 0 < x['own_node_rss_bytes'] < 8522825728
                            or not 0 < memory['physical_footprint_upper_bytes'] < 2080374784
                            or min(x['logical_bytes'], x['allocated_bytes']) < 0
                            or max(x['logical_bytes'], x['allocated_bytes']) >= 31675383808
                            or x['free_bytes'] <= 32749125632):
                        raise ValueError('resource')
                    result['retained_live_resource_records'] += 1
                except (ValueError, TypeError, KeyError):
                    finding(str(index)+':resources', 'RETAINED_RESOURCE_OUT_OF_BOUNDS')
        if last_sync is not None and r is not None:
            if any(last_sync.get(name) != r.get('last_'+name) for name in ('chain', 'network', 'peer_diagnostics')):
                finding('result', 'CORE_LAST_OBSERVATION_MISMATCH')
            if r.get('last_resources_observation') != last_sync.get('resources'):
                finding('result', 'CORE_LAST_RESOURCE_MISMATCH')
        if v is not None:
            if (v.get('live_resource_records_checked') != result['retained_live_resource_records']
                    or v.get('HTTP_first_timeouts') != timeout_events
                    or v.get('retained_completed_single_retry_successes') != retry_successes):
                finding('verification', 'CORE_OBSERVATION_COUNTS_MISMATCH')
        result.update(retained_timeout_events=timeout_events, retained_single_retry_successes=retry_successes)
        if not result['complete_consumer_observations'] or not result['retained_live_resource_records']:
            finding('events', 'CORE_OBSERVATIONS_MISSING', 'MISSING')
    if all(name in raw for name in ('pdf', 'proof', 'header')) and r is not None:
        try:
            link = ots.consume_ots_header_links(raw['pdf'], raw['proof'], [
                {'source_id': 'D199-retained-local-Core', 'claimed_height': 912095,
                 'block_hash_response': FIXED_HASH.encode('ascii'), 'header_response': raw['header']}])
            result['subject_link'] = link
            if link['header_binding']['status'] != 'OBSERVED' or link['standalone_pow']['status'] != 'OBSERVED':
                finding('subject-link', 'CORE_PUBLIC_SUBJECT_LINK_INVALID')
            if ('sample_header_verbose' in r and
                    r['sample_header_verbose']['result']['target'] != link['standalone_pow']['headers'][0]['target_hex']):
                finding('result:target', 'CORE_SAMPLE_FIELDS_INVALID')
        except (ValueError, TypeError, KeyError, IndexError):
            finding('subject-link', 'CORE_PUBLIC_SUBJECT_LINK_INVALID')
    result['status'] = ('REJECTED' if any(x['status'] == 'REJECTED' for x in findings)
                        else 'MISSING' if findings else 'OBSERVED')
    return result
