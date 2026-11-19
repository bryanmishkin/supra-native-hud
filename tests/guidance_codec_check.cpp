// Offline codec vectors only. No sockets, service loading, vehicle or renderer calls.
#include "guidance_payload.hpp"
#include <stdio.h>
using namespace supra_pip;
static void show(const GuidanceBytes& bytes){for(size_t i=0;i<bytes.size();++i)printf("%02x",bytes[i]);puts("");}
int main(){
    show(register_guidance(0,8301));show(attach_guidance(42,17));show(unregister_guidance());
    std::vector<std::pair<std::string,std::string> > options;
    show(register_displayable(0x321,0,800,480,options));
    options.push_back(std::make_pair(std::string("WindowCaption"),std::string("1056")));
    show(register_displayable(0x321,0,800,480,options));options.clear();
    options.push_back(std::make_pair(std::string("a"),std::string("bc")));
    options.push_back(std::make_pair(std::string("empty"),std::string("")));
    show(register_displayable(17,0,320,200,options));show(set_ric_maneuver_content(42,17));
    std::vector<GuidanceRequest> handshake=displayable_handshake(37,17,1,320,200,options);
    if(handshake.size()!=2 || handshake[0].request_type!=0x105u ||
       handshake[0].event_id!=0x80000004u || handshake[0].sequence!=37 ||
       !handshake[0].payload.empty() || handshake[1].request_type!=0x100u ||
       handshake[1].event_id!=4 || handshake[1].sequence!=37 ||
       handshake[1].payload!=register_displayable(17,1,320,200,options))return 1;
    std::vector<GuidanceRequest> release=displayable_release_requests(37);
    if(release.size()!=2 || release[0].request_type!=0x106u ||
       release[0].event_id!=0x80000004u || release[0].sequence!=37 ||
       !release[0].payload.empty() || release[1].request_type!=0x100u ||
       release[1].event_id!=6 || release[1].sequence!=37 || !release[1].payload.empty())return 3;
    bool rejected=false;
    try{displayable_handshake(0,17,1,320,200,options);}
    catch(const std::invalid_argument&){rejected=true;}
    if(!rejected)return 2;
    return 0;
}
