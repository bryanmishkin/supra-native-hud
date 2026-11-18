#ifndef SUPRA_FAULT_RECORD_HPP
#define SUPRA_FAULT_RECORD_HPP
#include <string>
#include <sstream>
#include <fstream>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
namespace supra {
inline std::string jsonString(const std::string& s){std::string out="\"";const char* hex="0123456789abcdef";for(size_t i=0;i<s.size();++i){unsigned char c=s[i];if(c=='"'||c=='\\'){out+='\\';out+=c;}else if(c<32||c>=127){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=c;}return out+'"';}
inline std::string recordTail(const std::string& path,unsigned limit){std::ifstream f(path.c_str(),std::ios::binary);if(!f)return "";f.seekg(0,std::ios::end);std::streamoff n=f.tellg();if(n<0)return "";if(n>(std::streamoff)limit)f.seekg(n-limit);else f.seekg(0);return std::string((std::istreambuf_iterator<char>(f)),std::istreambuf_iterator<char>());}
// One atomic file per record; sync the bytes before publishing its name.
inline bool durableRecord(const std::string& path,const std::string& body){
 std::string temp=path+".new";int fd=open(temp.c_str(),O_WRONLY|O_CREAT|O_TRUNC,0600);if(fd<0)return false;
 size_t at=0;bool ok=true;while(at<body.size()){ssize_t n=write(fd,body.data()+at,body.size()-at);if(n>0)at+=n;else if(n<0&&errno==EINTR)continue;else{ok=false;break;}}
 if(ok&&fsync(fd))ok=false;if(close(fd))ok=false;
 if(ok&&rename(temp.c_str(),path.c_str()))ok=false;
 if(ok)sync();else unlink(temp.c_str());return ok;
}
}
#endif
