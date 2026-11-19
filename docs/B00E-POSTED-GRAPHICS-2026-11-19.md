# Posted graphics evidence and IU marker intent

Owner direction, 19 November: record an **IU trident** as the distinct custom-image test, while independently tracing canvas configurations. See [IU test note](IU-TRIDENT-TEST.md). V1 and the vehicle remain untouched. No author contacted.

## Actual retained B00E resource uploads

Scanned 39 unique PCAP byte hashes in the local outputs, up to 64 MiB and 65,536 packets each. One capture failed strict TCP continuity and is recorded separately; unparsed streams are not evidence of absence. Duplicate file copies were excluded by hash.

277 decoded B00E method-3 request envelopes were found:

| Resource type / variant | Requests | Interpretation supported by payload |
| --- | ---: | --- |
| 3 / 4 | 270 | Text, including radio entries and the voice wait message |
| 10 / 11 | 7 | Composite text with nested text, including list titles |
| 1 / 2 | 0 | No retained B00E bitmap upload demonstrated in these parsed streams |

All counted envelopes have consistent lengths and repeated inner/outer resource identity/type. This scan establishes what the captures contain; it does not establish that the service rejects images. Factory clients can use pre-existing receiver resources.

## Firmware image producer lead

Captured HmiMain3D includes `CHmiICRicResourceManager::setRICBitmapResource` trace naming. Its playlist code also reports bitmap cover-art handles and byte streams (`CRhmiICPlaylistModel`). This supports tracing a real bitmap producer rather than assuming text-only service capability. String presence alone does not resolve the body encoder, model field or windshield placement. Direct string-pointer references were saved privately for continuation; instruction-looking words in data tables are not accepted as executed code.

## Next proof target

The independent configuration trace is checking the retained B00E create replies and model limits. Combine that evidence with the posted model/reference chain before constructing the IU marker transaction. Required: explicit image-bearing field, resource ownership, accepted encoding, receiver-advertised dimensions, visibility and removal. No change to the factory IDs 0x65/0x66/0x68/0x6e is authorized merely by decoding their existing traffic.

The IU test is recorded; a live larger-display test is not yet asserted ready. Do not repeat the failed PiP arrow experiment or request another discovery visit solely for this resource inventory.
