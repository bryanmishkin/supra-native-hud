# Canvas and rate session — 19 November 2026

Completed. V1 restarted and verified: installed baseline files/startup unchanged, read-only protection enabled, factory hooks and worker healthy, advancing RPM frames/heartbeat, temporary trial directory absent. Owner confirmed V1 visible and updating. All drawing cleanup passed.

## Confirmed observations

- The owner saw the 150×36 control cross and IU trident in both the windshield and gauge cluster.
- Both static controls completed their 30-second windows and resource removal checks.
- V1 installed files were verified against the accepted baseline before a clean pause. No persistent installation changes were made.

## Rate measurements

These are host-driven B006 transactions, not native application or visible display refresh limits. Original 240-fps video remains needed for visible-frame analysis.

| Case | Frames | Requested Hz | Schedule passed | Cleanup passed |
|---|---:|---:|---|---|
| hz-01 | 30 | 1 | True | True |
| hz-02 | 60 | 2 | True | True |
| hz-05 | 150 | 5 | True | True |
| hz-10 | 300 | 10 | True | True |
| hz-10-sustain-1 | 928 | 10 | False | True |
| hz-15 | 450 | 15 | True | True |
| hz-15-sustain-1 | 1001 | 15 | False | True |
| hz-20 | 600 | 20 | True | True |
| hz-20-sustain-1 | 1930 | 20 | False | True |
| hz-25-sustain-1 | 535 | 25 | False | True |
| hz-30 | 140 | 30 | False | True |
| hz-30-repeat | 900 | 30 | True | True |
| hz-30-sustain-1 | 84 | 30 | False | True |
| hz-40 | 18 | 40 | False | True |
| hz-40-repeat | 19 | 40 | False | True |

A 30-Hz, 30-second repeat completed 900 frames. Sustained confirmations did not establish a repeatable maximum. The 20-Hz and 10-Hz attempts each encountered approximately one second in the upload/post portion of a transaction. Those stalls do not establish a hardware refresh ceiling. The deadline check also includes scheduler lateness; a failure is not necessarily a receiver rejection.

The factory MODE source-menu capture completed: 4,731 packets, zero drops, exact Carousel model retained and idle focus/commit acknowledged. Both 36×36 cross and IU tests completed with upload/presence acknowledgments, exact factory-model restoration, and test-resource absence verified. Owner saw a square in the windshield only for the cross; the IU also appeared as only a square. Custom image detail is therefore unverified; do not label this successful bitmap binding. The dependent 128×128 ladder has not been run.

## Factory-content comparison

The exact current four-item factory Carousel was posted with its captured focus/commit sequence, without uploading a bitmap. The owner saw recognizable factory source icons/text. Withdrawal and exact model restoration were acknowledged. This establishes that the chosen model/focus reaches a visible factory menu; it does not establish type-1 bitmap support in the icon-reference field. Both distinct 36×36 bitmap candidates showed only a square. No 128×128 tests were run because custom image detail failed the prerequisite.

## Follow-up

Analyze the original slow-motion recording before claiming visible Hz. Investigate the receiver's handling of uploaded type-1 resources versus preinstalled type-7 icon references; do not move bitmap IDs into text or unknown fields without evidence. V1 code and persistent configuration remain outside this experiment.
