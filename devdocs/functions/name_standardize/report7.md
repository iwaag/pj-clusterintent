# Step 7 report: verification

## Summary

Step 7 is complete within the available local environment.

The local unit test suite and syntax checks pass. A full Nautobot UI/Job manual
scenario could not be executed in this workspace because Nautobot and Django are
not installed here, and no local compose/dev server definition is present.

To cover the same behavior, the manual scenario was reproduced with the local
pure Python evaluation and dnsmasq APIs.

## Local unit tests

Executed from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 61 tests in 0.005s
OK
```

## Syntax check

Executed from `nintent/`:

```text
python3 -m compileall nautobot_intent_catalog
```

Result:

```text
Compiling 'nautobot_intent_catalog/jobs.py'...
```

No compile errors were reported.

## Nautobot environment availability

Checked for a real local Nautobot runtime:

```text
command -v nautobot-server
```

Result:

```text
not found
```

Checked Python imports from `nintent/`:

```text
python3 -c "import django, nautobot"
```

Result:

```text
ModuleNotFoundError: No module named 'django'
```

Checked for local compose files:

```text
rg --files -g 'docker-compose.yml' -g 'compose.yaml' -g 'docker-compose.yaml' -g 'compose.yml'
```

Result:

```text
none found
```

Because of that, the actual Nautobot UI/Job run remains a follow-up for a real
Nautobot environment.

## Local manual scenario reproduction

Reproduced the requested flow with local objects and public package APIs:

1. Desired node: `pcmain`
2. Actual device candidate: `pcmain.local`
3. Primary endpoint with blank-derived names
4. Interface MAC fact: `AA-BB-CC-DD-EE-FF`
5. Node evaluation
6. Endpoint evaluation using node evaluation facts
7. dnsmasq export

Observed results:

```text
dns_name= pcmain.home.arpa
mdns_name= pcmain.local
node_status= partial
node_actual_refs= [{'object_type': 'dcim.device', 'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'name': 'pcmain.local'}]
endpoint_status= partial
dhcp_mac_candidates= [{'actual_node_ref': {'object_type': 'dcim.device', 'id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'name': 'pcmain.local'}, 'interface_id': 'cccccccc-cccc-cccc-cccc-cccccccccccc', 'interface_name': 'eth0', 'mac_address': 'aa:bb:cc:dd:ee:ff', 'enabled': True}]
```

The generated dnsmasq config contained both expected record types:

```text
host-record=pcmain.home.arpa,192.168.10.25
dhcp-host=aa:bb:cc:dd:ee:ff,pcmain.home.arpa,192.168.10.25
```

## Expected result coverage

Verified locally:

- desired endpoint DNS default: `pcmain.home.arpa`
- desired endpoint mDNS metadata default: `pcmain.local`
- node evaluation found exactly one actual node candidate: `pcmain.local`
- endpoint evaluation found exactly one MAC candidate:
  `aa:bb:cc:dd:ee:ff`
- dnsmasq export contained `host-record=`
- dnsmasq export contained `dhcp-host=`

Not verified locally:

- creating records through the Nautobot UI
- running `Evaluate Node Intent`, `Evaluate Endpoint Intent`, and
  `Export dnsmasq Records` as Nautobot Jobs

Those require installing the app into a real Nautobot environment.
