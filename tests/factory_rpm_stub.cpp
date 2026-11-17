// Host-only feed simulator for the unchanged drawing/cleanup integration.
#include "factory_rpm.hpp"
#include <time.h>
#include <cstdlib>
#include <cstring>
namespace supra {
static uint64_t initial=0;
static uint64_t ms(){timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return uint64_t(t.tv_sec)*1000+t.tv_nsec/1000000;}
bool startFactoryRpm(){initial=ms();return !getenv("SUPRA_TEST_FEED_UNAVAILABLE");}
Sample latestFactoryRpm(){Sample s;s.valid=true;s.value=6500;s.at=ms()/100*100;if(getenv("SUPRA_TEST_FEED_STALE")&&ms()-initial>400)s.at=initial;return s;}
}
