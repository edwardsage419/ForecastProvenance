"""Passive, bounded SHA256 OTS path interpretation; no chain or time verifier.

Format references: python-opentimestamps core timestamp/op/notary/serialize at
3af46432efc4a4c4e7bba439c1f49bce808eb3e5 (retained separately for reference).
This is an independent limited reader, not an imported/vendored OTS client.
"""
import hashlib
import json

MAGIC = bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')
BTC_TAG = bytes.fromhex('0588960d73d71901')
PENDING_TAG = bytes.fromhex('83dfe30d2ef90c8e')
URI_CHARS = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._/:')


def _service_json(raw):
    if type(raw) is not bytes or not 0 < len(raw) <= 65536:
        raise ValueError('PUBLIC_JSON_BYTES_OR_LIMIT')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('PUBLIC_JSON_DUPLICATE_KEY')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('PUBLIC_JSON_NONFINITE')

    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)
    if type(value) is not dict:
        raise ValueError('PUBLIC_JSON_OBJECT_REQUIRED')
    return value


def consume_public_chain_observations(header_response, claimed_height, requests, raw_artifacts):
    """Replay bounded external observations, never independent chain validation.

    Request origin labels and retained hashes describe local provenance only.
    Neither establishes independent services, trusted time, or canonical chain.
    """
    result = {'scope': 'PUBLIC_SERVICE_DECLARATIONS_ONLY_NOT_CHAIN_AUTHORITY',
              'sources': [], 'findings': [], 'chain_verification': 'NOT_CHECKED',
              'authenticated_time': 'NOT_ESTABLISHED',
              'source_independence': 'NOT_ESTABLISHED', 'tip_queries_atomic': False,
              'height_verification': 'PUBLIC_SERVICE_DECLARATION_ONLY',
              'project_subject_binding': 'NOT_ESTABLISHED'}
    findings = result['findings']

    def finding(item, status, error, local=None):
        row = {'item': item, 'status': status, 'error': error}
        findings.append(row)
        if local is not None:
            local.append(row)

    def verdict(items):
        return ('REJECTED' if any(row['status'] == 'REJECTED' for row in items) else
                'MISSING' if items else 'OBSERVED')

    try:
        header = _hex_response(header_response, 160)
        if type(claimed_height) is not int or not 0 <= claimed_height < 2**63:
            raise ValueError('PUBLIC_CLAIMED_HEIGHT')
        if type(requests) is not list or len(requests) > 16:
            raise ValueError('PUBLIC_REQUEST_RECORDS_LIMIT')
        if type(raw_artifacts) is not dict or len(raw_artifacts) > 8:
            raise ValueError('PUBLIC_RAW_RECORDS_LIMIT')
    except ValueError as error:
        finding('public-observations', 'REJECTED', str(error))
        return dict(result, status='REJECTED')
    block_hash = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
    expected = {'id': block_hash, 'height': claimed_height,
                'version': int.from_bytes(header[:4], 'little'),
                'timestamp': int.from_bytes(header[68:72], 'little'),
                'bits': int.from_bytes(header[72:76], 'little'),
                'nonce': int.from_bytes(header[76:80], 'little'),
                'merkle_root': header[36:68][::-1].hex(),
                'previousblockhash': header[4:36][::-1].hex()}
    bases = {'blockstream': 'https://blockstream.info/api', 'mempool': 'https://mempool.space/api'}
    paths = {'block': '/block/'+block_hash, 'status': '/block/'+block_hash+'/status',
             'tip-height': '/blocks/tip/height', 'tip-hash': '/blocks/tip/hash'}
    indexed, bound = {}, set()
    for index, row in enumerate(requests):
        if (type(row) is not dict or type(row.get('provider')) is not str
                or type(row.get('kind')) is not str
                or row['provider'] not in bases or row['kind'] not in paths):
            finding(str(index), 'REJECTED', 'PUBLIC_REQUEST_IDENTITY')
            continue
        key = (row['provider'], row['kind'])
        if key in indexed:
            finding('_'.join(key), 'REJECTED', 'PUBLIC_DUPLICATE_REQUEST')
            continue
        indexed[key] = row
    for source, base in bases.items():
        local, parsed = [], {}
        observation = {'source_id': source, 'findings': local,
                       'reported_depth_arithmetic': None}
        result['sources'].append(observation)
        for kind, path in paths.items():
            alias = source+'_'+kind; row = indexed.get((source, kind))
            if row is None:
                finding(alias, 'MISSING', 'PUBLIC_REQUEST_NOT_RETAINED', local)
                continue
            try:
                if row.get('url') != base+path:
                    raise ValueError('PUBLIC_REQUEST_URL_MISMATCH')
                if row.get('status') == 'FAILED':
                    finding(alias, 'MISSING', 'PUBLIC_SOURCE_FETCH_FAILED', local)
                    continue
                if row.get('status') != 'RETAINED' or row.get('final_url') != base+path or row.get('http_status') != 200:
                    raise ValueError('PUBLIC_REQUEST_RESULT')
                bound.add(alias)
                raw = raw_artifacts.get(alias)
                if raw is None:
                    finding(alias, 'MISSING', 'PUBLIC_RESPONSE_NOT_SUPPLIED', local)
                    continue
                if (type(raw) is not bytes or not 0 < len(raw) <= 65536
                        or type(row.get('bytes')) is not int or row['bytes'] != len(raw)
                        or row.get('sha256') != hashlib.sha256(raw).hexdigest()):
                    raise ValueError('PUBLIC_RESPONSE_IDENTITY_OR_LIMIT')
                if kind == 'block':
                    value = _service_json(raw)
                    for field, wanted in expected.items():
                        if type(value.get(field)) is not type(wanted) or value[field] != wanted:
                            raise ValueError('PUBLIC_METADATA_MISMATCH:'+field)
                elif kind == 'status':
                    value = _service_json(raw)
                    if type(value.get('in_best_chain')) is not bool:
                        raise ValueError('PUBLIC_BEST_CHAIN_BOOLEAN')
                    if 'height' in value and (type(value['height']) is not int or value['height'] != claimed_height):
                        raise ValueError('PUBLIC_STATUS_HEIGHT')
                    if 'next_best' in value:
                        next_hash = value['next_best']
                        if type(next_hash) is not str:
                            raise ValueError('PUBLIC_NEXT_HASH_FORMAT')
                        _hex_response(next_hash.encode('ascii'), 64)
                elif kind == 'tip-height':
                    text = raw.decode('ascii').removesuffix('\n')
                    if not 1 <= len(text) <= 19 or not text.isdigit() or int(text) >= 2**63:
                        raise ValueError('PUBLIC_TIP_HEIGHT_FORMAT')
                    value = int(text)
                else:
                    value = _hex_response(raw, 64).hex()
                parsed[kind] = value
            except (ValueError, UnicodeError, RecursionError) as error:
                finding(alias, 'REJECTED', str(error), local)
        if 'status' in parsed:
            observation['service_reported_in_best_chain'] = parsed['status']['in_best_chain']
        if 'tip-height' in parsed:
            observation['service_reported_tip_height'] = parsed['tip-height']
        if 'tip-hash' in parsed:
            observation['service_reported_tip_hash'] = parsed['tip-hash']
        if 'block' in parsed:
            observation['header_metadata_match'] = True
            observation['service_reported_sample_height'] = claimed_height
        if all(kind in parsed for kind in paths) and parsed['status']['in_best_chain']:
            if parsed['tip-height'] < claimed_height:
                finding(source, 'REJECTED', 'PUBLIC_TIP_BELOW_BEST_CHAIN_SAMPLE', local)
            else:
                observation['reported_depth_arithmetic'] = parsed['tip-height']-claimed_height+1
        observation['status'] = verdict(local)
    for alias in raw_artifacts:
        if alias not in bound:
            finding(str(alias), 'REJECTED', 'PUBLIC_UNBOUND_RESPONSE')
    return dict(result, status=verdict(findings))


class Reader:
    def __init__(self, raw):
        self.raw, self.position = raw, 0

    def take(self, count):
        end = self.position+count
        if count < 0 or end > len(self.raw):
            raise ValueError('OTS_TRUNCATED')
        result = self.raw[self.position:end]
        self.position = end
        return result

    def byte(self):
        return self.take(1)[0]

    def integer(self):
        result = 0
        for index in range(10):
            value = self.byte()
            result |= (value & 127) << (7*index)
            if value < 128:
                if index and value == 0:
                    raise ValueError('OTS_NONMINIMAL_INTEGER_UNSUPPORTED')
                return result
        raise ValueError('OTS_INTEGER_LIMIT')

    def variable(self, maximum, minimum=0):
        length = self.integer()
        if not minimum <= length <= maximum:
            raise ValueError('OTS_LENGTH_LIMIT')
        return self.take(length)

    def finish(self):
        if self.position != len(self.raw):
            raise ValueError('OTS_TRAILING_DATA')


def consume_ots_paths(subject_bytes, proof_bytes):
    """Read all supported paths from exact supplied bytes without any I/O.

    Supported file hash is SHA256; operations are SHA256, append, prepend,
    reverse and hexlify. Limits and stricter canonical integer/duplicate rules
    define this finite reader, not universal OTS protocol validity.
    Bitcoin heights/roots are declarations and computations, not chain facts.
    """
    if type(subject_bytes) is not bytes or type(proof_bytes) is not bytes:
        raise ValueError('OTS_BYTES_REQUIRED')
    if len(proof_bytes) > 1_048_576:
        raise ValueError('OTS_PROOF_SIZE_LIMIT')
    reader = Reader(proof_bytes)
    if reader.take(len(MAGIC)) != MAGIC or reader.byte() != 1 or reader.byte() != 8:
        raise ValueError('OTS_UNSUPPORTED_HEADER_VERSION_OR_FILE_HASH')
    digest = reader.take(32)
    if digest != hashlib.sha256(subject_bytes).digest():
        raise ValueError('OTS_SUBJECT_DIGEST_MISMATCH')
    body_start = reader.position
    result = {'scope': 'LOCAL_SUPPORTED_OTS_PATH_COMPUTATION_NOT_CHAIN_OR_TIME_VERIFICATION',
              'subject_digest_match': True, 'operation_count': 0, 'attestation_count': 0,
              'bitcoin_attestations': [], 'pending_attestations': [], 'unknown_attestations': [],
              'calendar_requests': 0, 'bitcoin_verification': 'NOT_CHECKED',
              'full_ots_verification': 'NOT_CHECKED', 'authenticated_time': 'NOT_ESTABLISHED'}
    nodes, reported_bytes = 0, 0

    def retain(collection, record):
        nonlocal reported_bytes
        reported_bytes += len(json.dumps(record, separators=(',', ':')).encode('ascii'))
        if reported_bytes > 1_048_576:
            raise ValueError('OTS_REPORT_SIZE_LIMIT')
        result[collection].append(record)

    def timestamp(message, path, depth):
        nonlocal nodes
        if depth >= 128:
            raise ValueError('OTS_DEPTH_LIMIT')
        seen = set()
        while True:
            tag = reader.byte()
            more = tag == 255
            if more:
                tag = reader.byte()
            nodes += 1
            if nodes > 4096:
                raise ValueError('OTS_NODE_LIMIT')
            if tag == 0:
                kind, payload = reader.take(8), reader.variable(8192)
                branch = (tag, kind, payload)
                if branch in seen:
                    raise ValueError('OTS_DUPLICATE_BRANCH_UNSUPPORTED')
                seen.add(branch)
                record = {'commitment_hex': message.hex(), 'path_ops': path}
                inner = Reader(payload)
                if kind == BTC_TAG:
                    if len(message) != 32:
                        raise ValueError('OTS_BITCOIN_COMMITMENT_LENGTH')
                    height = inner.integer()
                    inner.finish()
                    retain('bitcoin_attestations', dict(record, claimed_height=height))
                elif kind == PENDING_TAG:
                    uri = inner.variable(1000)
                    if any(value not in URI_CHARS for value in uri):
                        raise ValueError('OTS_PENDING_URI_INVALID')
                    inner.finish()
                    retain('pending_attestations', dict(record, uri=uri.decode('ascii')))
                else:
                    retain('unknown_attestations', dict(record, tag_hex=kind.hex(), payload_hex=payload.hex()))
                result['attestation_count'] += 1
            else:
                argument = reader.variable(4096, 1) if tag in (240, 241) else b''
                branch = (tag, argument)
                if branch in seen:
                    raise ValueError('OTS_DUPLICATE_BRANCH_UNSUPPORTED')
                seen.add(branch)
                if tag == 8:
                    following, operation = hashlib.sha256(message).digest(), {'op': 'SHA256'}
                elif tag in (240, 241):
                    following = message+argument if tag == 240 else argument+message
                    operation = {'op': 'APPEND' if tag == 240 else 'PREPEND', 'argument_hex': argument.hex()}
                elif tag == 242:
                    following, operation = message[::-1], {'op': 'REVERSE'}
                elif tag == 243:
                    following, operation = message.hex().encode('ascii'), {'op': 'HEXLIFY'}
                else:
                    raise ValueError('OTS_UNSUPPORTED_OPERATION_'+format(tag, '02x'))
                if not message or len(message) > 4096 or not following or len(following) > 4096:
                    raise ValueError('OTS_MESSAGE_OR_RESULT_LENGTH_LIMIT')
                result['operation_count'] += 1
                timestamp(following, path+[operation], depth+1)
            if not more:
                return

    timestamp(digest, [], 0)
    reader.finish()
    result.update(proof_bytes_consumed=reader.position, body_bytes_consumed=reader.position-body_start,
                  parsed_nodes=nodes, pending_or_unknown_evidence_is_not_bitcoin=True)
    return result


def _hex_response(raw, length):
    if type(raw) is not bytes:
        raise ValueError('HEADER_RESPONSE_BYTES_REQUIRED')
    if len(raw) not in (length, length+1):
        raise ValueError('HEADER_RESPONSE_LOWER_HEX_LENGTH')
    value = raw[:-1] if raw.endswith(b'\n') else raw
    if len(value) != length or any(c not in b'0123456789abcdef' for c in value):
        raise ValueError('HEADER_RESPONSE_LOWER_HEX_LENGTH')
    return bytes.fromhex(value.decode('ascii'))


MAINNET_POW_LIMIT = int('00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff', 16)


def decode_mainnet_pow_target(bits):
    """Bitcoin v30 compact/range subset, not required-difficulty validation."""
    if type(bits) is not int or not 0 <= bits <= 0xffffffff:
        raise ValueError('HEADER_TARGET_UINT32_REQUIRED')
    size, word = bits >> 24, bits & 0x007fffff
    if size <= 3:
        word >>= 8*(3-size)
    negative = word != 0 and bool(bits & 0x00800000)
    overflow = word != 0 and (size > 34 or (word > 0xff and size > 33)
                              or (word > 0xffff and size > 32))
    if negative or overflow or word == 0:
        raise ValueError('HEADER_TARGET_NEGATIVE_ZERO_OR_OVERFLOW')
    target = word if size <= 3 else word << (8*(size-3))
    if target > MAINNET_POW_LIMIT:
        raise ValueError('HEADER_TARGET_ABOVE_MAINNET_LIMIT')
    return target


def check_header_pow(header_response):
    """Check one supplied header against its own declared target, without I/O.

    Does not establish whether that target is correct for any claimed height,
    valid chain membership, cumulative work, confirmations or civil time.
    """
    raw = _hex_response(header_response, 160)
    digest = hashlib.sha256(hashlib.sha256(raw).digest()).digest()
    bits = int.from_bytes(raw[72:76], 'little')
    result = {'scope': 'STANDALONE_DECLARED_TARGET_MAINNET_LIMIT_ONLY',
              'block_hash': digest[::-1].hex(), 'declared_nbits_hex': format(bits, '08x'),
              'mainnet_pow_limit_hex': format(MAINNET_POW_LIMIT, '064x'),
              'chain_verification': 'NOT_CHECKED', 'required_target_at_height': 'NOT_CHECKED',
              'confirmations': 'NOT_CHECKED', 'authenticated_time': 'NOT_ESTABLISHED'}
    try:
        target = decode_mainnet_pow_target(bits)
    except ValueError as error:
        return dict(result, status='REJECTED', error=str(error))
    within = int.from_bytes(digest, 'little') <= target
    result.update(target_hex=format(target, '064x'), hash_within_declared_target=within,
                  status='OBSERVED' if within else 'REJECTED')
    if not within:
        result['error'] = 'HEADER_HASH_ABOVE_DECLARED_TARGET'
    return result


def consume_ots_header_links(subject_bytes, proof_bytes, header_records):
    """Bind computed Bitcoin paths to supplied public header bytes, without I/O.

    The original header_binding is byte consistency only. A separate standalone
    PoW sub-result now checks each declared target; callers must retain both.
    Neither establishes height, correct difficulty, chain, time or authority.
    """
    body = consume_ots_paths(subject_bytes, proof_bytes)
    binding = {'scope': 'PUBLIC_HEADER_BYTES_AND_PATH_CONSISTENCY_ONLY',
               'headers': [], 'links': [], 'findings': [],
               'height_verification': 'PUBLIC_SERVICE_DECLARATION_ONLY',
               'chain_verification': 'NOT_CHECKED', 'proof_of_work': 'NOT_CHECKED',
               'full_ots_verification': 'NOT_CHECKED', 'authenticated_time': 'NOT_ESTABLISHED',
               'project_subject_binding': 'NOT_ESTABLISHED'}
    findings, headers = binding['findings'], binding['headers']

    def finding(item, status, error):
        findings.append({'item': item, 'status': status, 'error': error})

    if type(header_records) is not list or len(header_records) > 32:
        finding('headers', 'REJECTED', 'HEADER_RECORDS_TYPE_OR_LIMIT')
        records = []
    else:
        records = header_records
    sources = set()
    for index, record in enumerate(records):
        try:
            if type(record) is not dict or set(record) != {
                    'source_id', 'claimed_height', 'block_hash_response', 'header_response'}:
                raise ValueError('HEADER_RECORD_FIELDS')
            source, height = record['source_id'], record['claimed_height']
            if (type(source) is not str or not 1 <= len(source) <= 128
                    or any(not 33 <= ord(c) <= 126 for c in source)):
                raise ValueError('HEADER_SOURCE_ID_FORMAT')
            if type(height) is not int or not 0 <= height < 2**63:
                raise ValueError('HEADER_HEIGHT_FORMAT')
            if source in sources:
                raise ValueError('HEADER_DUPLICATE_SOURCE_ID')
            sources.add(source)
            expected_hash = _hex_response(record['block_hash_response'], 64).hex()
            raw = _hex_response(record['header_response'], 160)
            block_hash = hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
            if block_hash != expected_hash:
                raise ValueError('HEADER_BLOCK_HASH_MISMATCH')
            headers.append({'index': index, 'source_id': source, 'claimed_height': height,
                            'block_hash': block_hash, 'header_raw_sha256': hashlib.sha256(raw).hexdigest(),
                            'merkle_wire_hex': raw[36:68].hex(),
                            'untrusted_header_time_uint32': int.from_bytes(raw[68:72], 'little'),
                            'header_time_role': 'UNAUTHENTICATED_FIELD_NOT_CIVIL_TIME',
                            'block_hash_response_sha256': hashlib.sha256(record['block_hash_response']).hexdigest(),
                            'header_response_sha256': hashlib.sha256(record['header_response']).hexdigest()})
        except ValueError as error:
            finding('header:'+str(index), 'REJECTED', str(error))
    used = set()
    for index, attestation in enumerate(body['bitcoin_attestations']):
        matching = [row for row in headers if row['claimed_height'] == attestation['claimed_height']]
        link = {'path_index': index, 'claimed_height': attestation['claimed_height'],
                'header_indices': [row['index'] for row in matching],
                'merkle_root_match': bool(matching) and all(
                    row['merkle_wire_hex'] == attestation['commitment_hex'] for row in matching)}
        binding['links'].append(link)
        if not matching:
            finding('path:'+str(index), 'MISSING', 'HEADER_FOR_CLAIMED_HEIGHT_NOT_SUPPLIED')
        else:
            used.update(row['index'] for row in matching)
            if not link['merkle_root_match']:
                finding('path:'+str(index), 'REJECTED', 'HEADER_MERKLE_ROOT_MISMATCH')
    for row in headers:
        if row['index'] not in used:
            finding('header:'+str(row['index']), 'REJECTED', 'HEADER_WITHOUT_MATCHING_PROOF_HEIGHT')
    if not body['bitcoin_attestations']:
        finding('proof', 'MISSING', 'BITCOIN_ATTESTATION_NOT_SUPPLIED')
    binding['status'] = ('REJECTED' if any(row['status'] == 'REJECTED' for row in findings)
                         else 'MISSING' if findings else 'OBSERVED')
    pow_result = {'scope': 'STANDALONE_DECLARED_TARGET_MAINNET_LIMIT_ONLY',
                  'headers': [], 'findings': [], 'chain_verification': 'NOT_CHECKED',
                  'required_target_at_height': 'NOT_CHECKED', 'confirmations': 'NOT_CHECKED',
                  'authenticated_time': 'NOT_ESTABLISHED'}
    if type(header_records) is not list or len(header_records) > 32:
        pow_result['findings'].append({'item': 'headers', 'status': 'REJECTED',
                                       'error': 'HEADER_RECORDS_TYPE_OR_LIMIT'})
    elif not records:
        pow_result['findings'].append({'item': 'headers', 'status': 'MISSING',
                                       'error': 'HEADERS_NOT_SUPPLIED'})
    for index, record in enumerate(records):
        item = 'header:'+str(index)
        if type(record) is not dict:
            pow_result['findings'].append({'item': item, 'status': 'REJECTED', 'error': 'HEADER_RECORD_FIELDS'})
            continue
        if 'header_response' not in record:
            pow_result['findings'].append({'item': item, 'status': 'MISSING', 'error': 'HEADER_NOT_SUPPLIED'})
            continue
        try:
            checked = check_header_pow(record['header_response'])
            pow_result['headers'].append(dict(checked, index=index))
            if checked['status'] == 'REJECTED':
                pow_result['findings'].append({'item': item, 'status': 'REJECTED', 'error': checked['error']})
        except ValueError as error:
            pow_result['findings'].append({'item': item, 'status': 'REJECTED', 'error': str(error)})
    pow_result['status'] = ('REJECTED' if any(row['status'] == 'REJECTED' for row in pow_result['findings'])
                             else 'MISSING' if pow_result['findings'] else 'OBSERVED')
    return {'body_computation': body, 'header_binding': binding, 'standalone_pow': pow_result}
