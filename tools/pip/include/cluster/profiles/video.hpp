#pragma once
#include <stdint.h>

// Experimental Supra frame envelope. This is NOT a proven HUD output profile.
// Screen backing is measured locally; resource size stays below the decoded
// Supra 320x320 PiP maximum. Metadata convention is credited in vendor/ryseek-pip.
namespace nbt { namespace cluster {
struct VideoProfile {
    enum { BackingWidth=800, BackingHeight=480, ContentWidth=320,
        ContentHeight=200, ContentY=1, CompactWidth=160, CompactHeight=100,
        DisplayCount=2, DisplayIndex=1, WindowIdLength=9,
        ScreenFormat=8, ScreenUsage=6, ScreenTransparency=0, ScreenAlpha=255,
        ScreenZOrder=1000, ScreenContextFlags=1,
        MetadataMap=0, MetadataManeuver=1, MetadataBytes=84 };
    static uint32_t maneuver;
    static const char* windowId() { return "268444457"; }
    static bool encodeMetadataBgra(uint8_t* p, uint16_t picture, unsigned profile) {
        if (profile != MetadataManeuver || maneuver < 0x0f000000u ||
            maneuver > 0x0f000004u) return false;
        for (unsigned i=0;i<MetadataBytes;++i) p[i]=0;
        p[0]=uint8_t(picture>>8); p[1]=uint8_t(picture);
        p[4]=1; p[7]=1;
        // Hypothesis: G30's 0f000000 corresponds to its description ID.
        // This variable binding is tested, not claimed as Supra acceptance.
        p[16]=uint8_t(maneuver>>24); p[17]=uint8_t(maneuver>>16);
        p[18]=uint8_t(maneuver>>8); p[19]=uint8_t(maneuver);
        return true;
    }
};
} }
