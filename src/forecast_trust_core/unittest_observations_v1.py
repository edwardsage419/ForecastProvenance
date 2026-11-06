"""Pure finite local unittest identity/lifecycle comparison, shared by consumer and test capture.

No I/O, protocol IDs, signing, runtime truth, applicability or authority.
"""

def _context(invocation_id, attempt_index):
    if type(invocation_id) is not str or not invocation_id or type(attempt_index) is not int or attempt_index < 1:
        raise ValueError('Invalid local invocation/attempt')


def _key(identity):
    if type(identity) is not dict or set(identity) != {'test_path', 'class_name', 'method_name', 'case_keys'}:
        raise ValueError('Invalid structured identity')
    if any(type(identity[k]) is not str or not identity[k] for k in ('test_path', 'class_name', 'method_name')):
        raise ValueError('Invalid method identity')
    cases = identity['case_keys']
    if type(cases) is not list or any(type(k) is not str or not k for k in cases):
        raise ValueError('Invalid case keys')
    return (identity['test_path'], identity['class_name'], identity['method_name'], tuple(cases))


def compare_events(expected, events, invocation_id, attempt_index):
    """Finite local consistency only. Missing records never become success."""
    _context(invocation_id, attempt_index)
    wanted = {}
    for identity in expected:
        key = _key(identity)
        if key in wanted:
            raise ValueError('Duplicate expected identity')
        wanted[key] = identity
    if not wanted or any(k[:3] + ((),) not in wanted for k in wanted):
        raise ValueError('Nonempty expectations with explicit parent required')
    seen = {}; errors = []; extra = []; duplicate = []; failed = []
    active = None; starts = 0; stopped = False; started = False
    started_methods = set()
    base = {'sequence', 'event', 'invocation_id', 'attempt_index'}
    result_kinds = {'METHOD_RESULT', 'SUBTEST_RESULT'}
    for index, row in enumerate(events):
        if type(row) is not dict:
            errors.append('EVENT_SHAPE'); continue
        event = row.get('event')
        if type(event) is not str:
            errors.append('EVENT_SHAPE'); continue
        fields = base | ({'identity'} if event in {'METHOD_START', 'METHOD_STOP'} else
                         {'identity', 'outcome'} if event in result_kinds else
                         {'tests_run', 'was_successful'} if event == 'RUN_STOP' else set())
        if set(row) != fields or type(row.get('sequence')) is not int or row['sequence'] != index:
            errors.append('EVENT_SHAPE_OR_SEQUENCE')
            continue  # malformed observations cannot supply results or lifecycle state
        if row.get('invocation_id') != invocation_id or type(row.get('attempt_index')) is not int or row['attempt_index'] != attempt_index:
            errors.append('WRONG_INVOCATION_ATTEMPT'); continue
        if stopped or (index == 0 and event != 'RUN_START'):
            errors.append('RUN_LIFECYCLE')
        if event == 'RUN_START':
            if started or index != 0: errors.append('RUN_LIFECYCLE')
            started = True; continue
        if event == 'RUN_STOP':
            stopped = True
            if active is not None or type(row.get('tests_run')) is not int or row.get('tests_run') != starts or row.get('was_successful') is not True:
                errors.append('RUN_INCOMPLETE_OR_UNSUCCESSFUL')
            continue
        if event not in {'METHOD_START', 'METHOD_STOP'} | result_kinds:
            errors.append('UNSUPPORTED_EVENT'); continue
        try: key = _key(row.get('identity'))
        except ValueError:
            errors.append('IDENTITY_SHAPE'); continue
        parent = key[:3] + ((),)
        if event == 'METHOD_START':
            if active is not None or key != parent: errors.append('METHOD_LIFECYCLE')
            if key not in wanted or key in started_methods:
                errors.append('EXTRA_OR_REPEATED_METHOD')
            started_methods.add(key)
            active = key; starts += 1
        elif event == 'METHOD_STOP':
            if key != active or key != parent: errors.append('METHOD_LIFECYCLE')
            active = None
        else:
            if active != parent or ((event == 'METHOD_RESULT') != (key == parent)):
                errors.append('WRONG_PARENT_OR_NODE_KIND'); continue
            if event == 'SUBTEST_RESULT' and parent in seen:
                errors.append('CHILD_AFTER_PARENT_RESULT')
            if key not in wanted: extra.append(row['identity'])
            if key in seen: duplicate.append(row['identity'])
            seen[key] = row['outcome']
            if row['outcome'] != 'SUCCESS': failed.append(row['identity'])
    if not started or not stopped or active is not None: errors.append('RUN_INCOMPLETE')
    missing = [identity for key, identity in wanted.items() if key not in seen]
    return {'finite_observations_match': not (errors or extra or duplicate or failed or missing),
            'missing': missing, 'failed': failed, 'extra': extra, 'duplicate': duplicate,
            'errors': errors, 'scope': 'FINITE_LOCAL_DEVELOPMENT_OBSERVATIONS_ONLY',
            'actual_profile_binding': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
            'protocol_state_change': 'NONE'}


