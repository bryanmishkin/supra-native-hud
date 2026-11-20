# Root viewport investigation: transport and native service coverage

Offline work on 20 November. V1 application, startup and installed files are unchanged. The owner is disconnected. This does not establish a larger windshield drawing surface.

## Previously missing transport coverage

`tools/audit_hud_udp.py` now examines retained Ethernet/IPv4 UDP captures in addition to the prior TCP analysis. The corpus contains 52 unique PCAPs by SHA256, 125624 UDP datagrams and 117898 SOME/IP service-discovery messages. All 52 parse without a capture/SD error. The 298 distinct discovery entry shapes include offers, finds and subscriptions; they are not 298 services or drawing surfaces.

Each entry retains a first-evidence capture hash, packet number, timestamp and flow in the private report. Endpoint inventory includes only nonzero-TTL OfferService entries with IPv4 endpoint options. Stop offers and subscriptions are not promoted to active offers. The inventory shows what was advertised during retained recordings, not what is currently running or every interface the vehicle could expose.

The actual cluster endpoint advertises these application services:

| Service | Captured transport | Meaning / boundary |
| --- | --- | --- |
| B006 | TCP and UDP | Existing RIC resource/model interface; road image limits are not root viewport dimensions |
| B009 | TCP and UDP | Existing DisplaySink negotiation; observed PiP selection remains cluster 1 |
| B00E | TCP and UDP | Existing HUD menu model path; factory frame does not prove arbitrary interior pixels |
| B011 v2 | TCP and UDP | Native KombiInterface_2; no root rectangle setter established |
| B00A | TCP and UDP | Newly matched native ConsumptionHistory client, not a demonstrated viewport API |

No non-discovery SOME/IP UDP application message in this retained corpus uses the cluster endpoint. The offers prove advertised transports; they do not demonstrate a working UDP drawing transaction. The existing drawing observations and application traffic remain separate TCP evidence.

Private endpoint addresses and captures are not published in this repository. An advertised UDP binding does not justify replaying TCP methods over UDP or assuming equivalent request/ACK semantics.

The two unclassified UDP flow groups are 2167 eight-byte multicast datagrams and 460 datagrams on multicast-DNS port 5353. Neither is decoded as a pixel transport. Small control messages could still affect rendering; payload size alone does not rule that out. No hidden full-image upload is claimed from these records.

## Exact native mappings, not service-number guesses

Captured HmiMain3D SHA256 `fe770d1957fdfcd250d1f8cf7fba0e9a7c25e8c053e59f04f3274055fedda935` provides 16 constructor-to-service-to-RTTI matches. In particular:

- B00A registration at`0x27ea978` establishes `CSomeIPConsumptionHistoryClientBase`. `requestGetConsumptionHistory` at`0x27e74a0` sends method 8 without a member payload. `requestSetScalingDistance` at`0x27e8d84` sends method 0x11; serializer`0x27e8ce8` accepts a one-byte enum 0..3. This is not evidence of screen width, height or scaling.
- B004 registration at`0x27eef98` establishes `CSomeIPAshellMsgHandlerClientBase`. The generated HMI notification decoder expects a u32 byte-extent prefix followed by eight-byte records. **None of the 285 retained B004/8002 bodies matches that outer-length contract.** Their flow is separate from the cluster. The private extraction preserves the mismatch and raw blocks; it does not invent a HUD/CAN schema.
- 3003 registration at`0x274ad4c` establishes `CSomeIPXView3DClientBase`; this name alone is not a windshield binding.
- B005 maps to KombiInterface, but it was not offered by the cluster in these retained announcements. B530 has not been matched to this constructor family.

## Reproducible offline check

Run from the repository with your private capture directory:

```sh
python3 tools/audit_hud_udp.py /absolute/private/captures /absolute/private/udp-corpus.json
python3 -m unittest discover -s tools -p test_audit_hud_udp.py -v
```

Eight tests verify capture deduplication and packet provenance, complete capture-to-offer decoding, concatenated message boundaries, rejection of truncated records and UDP fragments, rejection of malformed option references/extents, unsupported SOME/IP-TP rejection, and exclusion of stop offers/subscriptions from endpoint inventory.

Limitations: classic microsecond Ethernet PCAP only; IPv4 UDP only; no checksum authentication, fragmentation reassembly, SOME/IP-TP, MOST/CAN, missing traffic or receiver firmware coverage. The tool does not contact any vehicle or grant drawing permission.
