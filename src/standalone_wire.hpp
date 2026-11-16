#ifndef SUPRA_STANDALONE_WIRE_HPP
#define SUPRA_STANDALONE_WIRE_HPP
#include <vector>
#include <stdint.h>
#include <string>
namespace supra {
typedef std::vector<unsigned char> Bytes;
struct Command {unsigned method;Bytes body;};
struct Profile {std::vector<Command> setup,cleanup;};
unsigned read32(const Bytes&,unsigned);
void put32(Bytes&,unsigned);
void set32(Bytes&,unsigned,unsigned);
Profile readProfile(const char*);
Bytes encodeRle(const Bytes&,bool swap);
Bytes bitmapBody(unsigned,const Bytes&);
Bytes checkBody(unsigned);
Bytes removeBody(unsigned);
Bytes request(unsigned,unsigned,const Bytes&);
Bytes response(unsigned,unsigned,const Bytes&);
}
#endif
