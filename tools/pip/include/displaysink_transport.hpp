// Owned DisplaySink control transport. No Guidance, Screen, or V1 operations.
// Captured Supra tuple is Kombi, NOT a windshield pixel-delivery grant.
#ifndef SUPRA_DISPLAYSINK_TRANSPORT_HPP
#define SUPRA_DISPLAYSINK_TRANSPORT_HPP
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

namespace supra_pip {
class DisplaySink {
    int tcp_, udp_;
    sockaddr_in peer_, local_;
    unsigned sequence_, used_;
    uint8_t input_[64];
    double end_, renew_, lease_;
    bool subscribed_, selected_, failed_, pending_, attempted_;
    DisplaySink(const DisplaySink&);
    DisplaySink& operator=(const DisplaySink&);
    static unsigned get16(const uint8_t* p) { return unsigned(p[0])*256+p[1]; }
    static unsigned get32(const uint8_t* p) { return get16(p)*65536u+get16(p+2); }
    static void put16(uint8_t* p,unsigned x) { p[0]=x>>8;p[1]=x; }
    static double now() {
        timespec t; if(clock_gettime(CLOCK_MONOTONIC,&t)) return -1;
        return double(t.tv_sec)+double(t.tv_nsec)/1e9;
    }
    static bool nonblock(int fd) {
        int flags=fcntl(fd,F_GETFL,0);
        return flags>=0 && fcntl(fd,F_SETFL,flags|O_NONBLOCK)==0;
    }
    static bool wait(int fd,short events,double deadline) {
        for (;;) {
            double left=deadline-now(); if(left<=0 || left>60) return false;
            pollfd p={fd,events,0}; int r=poll(&p,1,int(left*1000)+1);
            if(r<0 && errno==EINTR) continue;
            return r>0 && !(p.revents&(POLLERR|POLLNVAL)) && (p.revents&events);
        }
    }
    bool write_all(const uint8_t* data,unsigned n,double deadline) {
        while(n) {
            if(!wait(tcp_,POLLOUT,deadline)) return false;
#ifdef MSG_NOSIGNAL
            int flags=MSG_NOSIGNAL;
#else
            int flags=0;
#endif
            ssize_t k=send(tcp_,data,n,flags);
            if(k<0 && (errno==EINTR || errno==EAGAIN || errno==EWOULDBLOCK)) continue;
            if(k<=0) return false;
            data+=k;n-=unsigned(k);
        }
        return true;
    }
    bool subscribe(unsigned ttl) {
        uint8_t p[56]={0};
        p[0]=p[1]=255;p[2]=0x81;p[7]=48;
        put16(p+10,sequence_);p[12]=p[13]=1;p[14]=2;p[16]=0xc0;
        p[23]=16;p[24]=6;p[27]=0x10;put16(p+28,0xb009);
        p[31]=p[32]=1;p[35]=ttl;p[39]=1;p[43]=12;p[45]=9;p[46]=4;
        memcpy(p+48,&local_.sin_addr,4);p[53]=6;memcpy(p+54,&local_.sin_port,2);
        // A bounded 30-second session cannot wrap this counter.
        ++sequence_;
        ssize_t n=sendto(udp_,p,sizeof(p),0,reinterpret_cast<sockaddr*>(&peer_),sizeof(peer_));
        if(n!=sizeof(p)) return false;
        subscribed_=ttl!=0;renew_=now()+1.0;return true;
    }
    bool receive_ack() {
        uint8_t p[2048];sockaddr_in source; socklen_t size=sizeof(source);
        ssize_t n=recvfrom(udp_,p,sizeof(p),0,reinterpret_cast<sockaddr*>(&source),&size);
        if(n<0) return errno==EINTR || errno==EAGAIN || errno==EWOULDBLOCK;
        if(size!=sizeof(source) || source.sin_addr.s_addr!=peer_.sin_addr.s_addr ||
           source.sin_port!=peer_.sin_port) return true; // unrelated sender cannot grant a lease
        // Strict retained single-entry ACK. Offers/bundles are not ACK grants.
        if(n!=44 || get16(p)!=0xffff || get16(p+2)!=0x8100 || get32(p+4)!=36 ||
           get16(p+8)!=0 || !get16(p+10) || memcmp(p+12,"\1\1\2\0",4) ||
           (p[16]!=0x40 && p[16]!=0xc0) || p[17] || p[18] || p[19] ||
           get32(p+20)!=16 || p[24]!=7 || p[25] || p[26] || p[27] ||
           get16(p+28)!=0xb009 || get16(p+30)!=1 || p[32]!=1 ||
           get32(p+36)!=1 || get32(p+40)!=0) return false;
        unsigned ttl=(unsigned(p[33])<<16)|(unsigned(p[34])<<8)|p[35];
        if(!ttl || ttl>3) return false;
        lease_=now()+ttl;return true;
    }
    bool receive_selection() {
        ssize_t n=recv(tcp_,input_+used_,sizeof(input_)-used_,0);
        if(n<0) return errno==EINTR || errno==EAGAIN || errno==EWOULDBLOCK;
        if(n==0) return false;
        used_+=unsigned(n);
        while(used_>=16) {
            unsigned size=get32(input_+4);
            if(size<8 || size>56) return false;
            size+=8;if(used_<size) break;
            const uint8_t cookie[16]={255,255,128,0,0,0,0,8,222,173,190,239,1,1,2,0};
            if(size==16 && !memcmp(input_,cookie,16)) {
                // No selection or lease change from a keepalive cookie.
            } else {
                selected_=false;
                const uint8_t tail[17]={1,1,2,0,0x3f,0xf0,0,0,0,0,0,0,1,0xcc,0,0xed,1};
                if(size!=29 || get16(input_)!=0xb009 || get16(input_+2)!=0x8001 ||
                   get32(input_+8)!=0 || memcmp(input_+12,tail,sizeof(tail))) return false;
                if(pending_) return false;
                pending_=true; // UDP ACK and TCP event can arrive in either order.
            }
            used_-=size;memmove(input_,input_+size,used_);
        }
        return used_<sizeof(input_);
    }
public:
    DisplaySink():tcp_(-1),udp_(-1),sequence_(1),used_(0),end_(0),renew_(0),lease_(0),
        subscribed_(false),selected_(false),failed_(false),pending_(false),attempted_(false) { memset(&peer_,0,sizeof(peer_));memset(&local_,0,sizeof(local_)); }
    ~DisplaySink() { close(); }
    // No default addresses; no SO_REUSE*, factory port reuse, or address setup.
    // Caller must independently establish producer identity/ownership before deployment.
    bool open(const char* producer,const char* receiver,unsigned sink_port,unsigned sd_port,unsigned seconds) {
        if(attempted_ || tcp_>=0 || udp_>=0 || failed_ || !seconds || seconds>30 ||
           !sink_port || sink_port>65535 || !sd_port || sd_port>65535) return false;
        attempted_=true;
        if(now()<0) return fail();
        local_.sin_family=peer_.sin_family=AF_INET;
        if(inet_pton(AF_INET,producer,&local_.sin_addr)!=1 || inet_pton(AF_INET,receiver,&peer_.sin_addr)!=1 ||
           !local_.sin_addr.s_addr || !peer_.sin_addr.s_addr ||
           local_.sin_addr.s_addr==INADDR_BROADCAST || peer_.sin_addr.s_addr==INADDR_BROADCAST ||
           IN_MULTICAST(ntohl(local_.sin_addr.s_addr)) || IN_MULTICAST(ntohl(peer_.sin_addr.s_addr))) return false;
        end_=now()+seconds;peer_.sin_port=htons(sink_port);
        tcp_=socket(AF_INET,SOCK_STREAM,0);
#ifdef SO_NOSIGPIPE
        int yes=1;if(tcp_>=0 && setsockopt(tcp_,SOL_SOCKET,SO_NOSIGPIPE,&yes,sizeof(yes))) return fail();
#endif
        if(tcp_<0 || !nonblock(tcp_) || bind(tcp_,reinterpret_cast<sockaddr*>(&local_),sizeof(local_))) return fail();
        int c=connect(tcp_,reinterpret_cast<sockaddr*>(&peer_),sizeof(peer_));
        if(c && errno!=EINPROGRESS) return fail();
        double deadline=now()+1;if(deadline>end_) deadline=end_;
        int error=0;socklen_t len=sizeof(error);
        if(!wait(tcp_,POLLOUT,deadline) || getsockopt(tcp_,SOL_SOCKET,SO_ERROR,&error,&len) || error) return fail();
        len=sizeof(local_);if(getsockname(tcp_,reinterpret_cast<sockaddr*>(&local_),&len)) return fail();
        sockaddr_in sender=local_;sender.sin_port=0;
        udp_=socket(AF_INET,SOCK_DGRAM,0);peer_.sin_port=htons(sd_port);
        if(udp_<0 || !nonblock(udp_) || bind(udp_,reinterpret_cast<sockaddr*>(&sender),sizeof(sender)) || !subscribe(3)) return fail();
        return true;
    }
    bool fail() { failed_=true;selected_=false;close();return false; }
    bool pump() {
        if(failed_ || tcp_<0 || udp_<0 || now()<0 || now()>=end_) return fail();
        if(lease_ && now()>=lease_) return fail();
        if(now()>=renew_ && !subscribe(3)) return fail();
        pollfd p[2]={{udp_,POLLIN,0},{tcp_,POLLIN,0}};
        int n=poll(p,2,20);
        if(n<0) return errno==EINTR ? true : fail();
        for(unsigned i=0;i<2;++i) if(p[i].revents&(POLLERR|POLLHUP|POLLNVAL)) return fail();
        if((p[0].revents&POLLIN) && !receive_ack()) return fail();
        if((p[1].revents&POLLIN) && !receive_selection()) return fail();
        if(pending_ && lease_>now()) {
            const uint8_t done[18]={0xb0,9,0,1,0,0,0,10,0,1,0,0,1,1,1,0,1,0};
            double deadline=now()+0.25;
            if(deadline>lease_) deadline=lease_;
            if(deadline>end_) deadline=end_;
            if(!write_all(done,sizeof(done),deadline) || now()>=lease_) return fail();
            pending_=false;selected_=true;
        }
        return true;
    }
    bool negotiated_cluster() const { double t=now();return selected_ && !failed_ && t>=0 && t<lease_ && t<end_; }
    bool close() {
        selected_=false;pending_=false;bool released=true;
        if(subscribed_ && udp_>=0) released=subscribe(0);
        if(tcp_>=0) ::close(tcp_);
        if(udp_>=0) ::close(udp_);
        tcp_=udp_=-1;subscribed_=false;used_=0;lease_=0;
        // released means unsubscribe SENT, not receiver image-removal confirmed.
        return released;
    }
};
}
#endif
