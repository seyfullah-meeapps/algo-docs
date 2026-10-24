"""Execute source-extracted C++ password handlers with fake DB/session adapters.

Windows/MSVC only. No network, credentials, source writes or real QuickFIX/DB.
This is a focused handler test, not a full application integration test.
"""
import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path


def function(source, signature):
    start = source.index(signature)
    # Preserve offsets while hiding comments and quoted braces.
    masked = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
                    lambda m: ' ' * len(m.group()), source)
    opening = masked.index('{', start)
    depth = 0
    for pos in range(opening, len(masked)):
        depth += (masked[pos] == '{') - (masked[pos] == '}')
        if depth == 0:
            return source[start:pos + 1]
    raise ValueError('Unclosed function: ' + signature)


ADAPTERS = r'''
#include <string>
#include <map>
#include <mutex>
#include <optional>
#include <functional>
#include <memory>
#include <iostream>
#include <stdexcept>
#define LOG_CRIT(...) ((void)0)
#define EXCEPT(...)
namespace FIX {
using MsgType = std::string;
const std::string MsgType_Logon="A", MsgType_Logout="5";
struct Header { std::string type; void getField(std::string& s) const { s=type; } };
struct Message {
 Header header; std::map<int,std::string> fields;
 const Header& getHeader() const { return header; }
 bool isSetField(int tag) const { return fields.count(tag)!=0; }
 std::string getField(int tag) const { return fields.at(tag); }
};
struct SessionID {
 std::string qualifier;
 SessionID(const char* q):qualifier(q) {}
 const std::string& getSessionQualifier() const { return qualifier; }
};
struct Session {
 static Session* lookupSession(const std::string&) { static Session s; return &s; }
 void logout(const std::string&) {}
};
}
struct FakeDB {
 std::string password="A", pending;
 bool fail=false;
 int writes=0;
 bool UpdateOrderUserPassword(const std::string&,const std::string& p,const std::string& q) {
  ++writes; if(fail) return false; password=p; pending=q; return true;
 }
};
class SdkSessionManager {
public:
 struct State {
  std::string live,db_pw,db_pending,armed;
  bool auto_flow=false,pending_recovery_tried=false;
  int renew_attempts=0;
 };
 struct Config { std::map<std::string,std::string> newPasswords; bool autoRenewExpiredPasswords=false; };
 Config fix_session_config_;
 std::mutex fix_pw_mutex_;
 std::map<std::string,State> fix_pw_;
 std::shared_ptr<FakeDB> user_service_=std::make_shared<FakeDB>();
 void SpawnFixPwWorker(std::function<void()> fn) { fn(); }
 void RenewExpiredFixPassword(const std::string&) {}
 void seedFixPassword(const std::string&,const std::string&,const std::string&);
 std::optional<std::string> armFromConfig(const std::string&,const std::string&,const std::string&);
 void onFixPasswordChangeResult(const std::string&,int);
 void onUserConnected(const std::string&);
 bool FixPasswordPromoteNeeded(const std::string&);
 void PromoteFixPasswordIfNeeded(const std::string&);
};
struct FixEngine {
 struct User { struct Creds { std::string username="fake",password="A"; } credentials;
  std::string fix_new_password; };
 struct Entry { User user; std::string session_id="fake"; };
 struct Callbacks {
  std::function<void(const std::string&,int)> onFixPasswordChangeResult,onFixLogonRejected;
 };
 std::map<std::string,Entry> sessions_;
 std::mutex creds_mutex_;
 Callbacks* callbacks_=nullptr;
 void track_replay(Entry&,const FIX::Message&) {}
 void fromAdmin(const FIX::Message&,const FIX::SessionID&);
};
using OuchUser=FixEngine::User;
void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
'''

SCENARIOS = r'''
int main() {
 try {
  for(int status : {-1,0,1}) {
   SdkSessionManager host;
   host.seedFixPassword("fake","A","");
   host.fix_session_config_.newPasswords["fake"]="B";
   auto candidate=host.armFromConfig("fake","A","");
   require(candidate.has_value(),"fixture: config candidate absent");
   FixEngine sdk;
   sdk.sessions_["fake"].user.fix_new_password=*candidate;
   FixEngine::Callbacks cb;
   cb.onFixPasswordChangeResult=[&](const std::string& u,int s){host.onFixPasswordChangeResult(u,s);};
   sdk.callbacks_=&cb;
   FIX::Message logon; logon.header.type="A";
   if(status!=-1) logon.fields[1409]=std::to_string(status);
   sdk.fromAdmin(logon,"fake");
   // QuickFIX onLogon boundary: execute host's real onUserConnected handler.
   host.onUserConnected("fake");
   require(sdk.sessions_["fake"].user.credentials.password=="B","SDK did not adopt candidate");
   require(host.user_service_->pending.empty(),"pending not cleared by promotion");
   if(status==-1) {
    require(host.user_service_->password=="A","K233 observation changed; re-review source");
    require(host.fix_pw_["fake"].live=="A","host live unexpectedly advanced");
    std::cout<<"OBSERVED K233: absent 1409 -> SDK=B, DB=A, pending empty\n";
   } else {
    require(host.user_service_->password=="B","explicit success did not promote B");
    std::cout<<"CONTROL PASS: explicit 1409="<<status<<" -> SDK=DB=B\n";
   }
  }
  SdkSessionManager failed;
  failed.seedFixPassword("fake","A","");
  failed.fix_session_config_.newPasswords["fake"]="B";
  failed.user_service_->fail=true;
  auto result=failed.armFromConfig("fake","A","");
  require(result && *result=="B","K234 observation changed; re-review source");
  require(failed.user_service_->writes==1 && failed.user_service_->pending.empty(),"fixture DB state unexpected");
  require(failed.fix_pw_["fake"].armed=="B","candidate not armed in host");
  std::cout<<"OBSERVED K234: failed pending write still returns candidate B\n";
  SdkSessionManager control;
  control.seedFixPassword("fake","A","P");
  control.fix_session_config_.newPasswords["fake"]="B";
  require(!control.armFromConfig("fake","A","P"),"existing pending was overwritten");
  require(control.user_service_->writes==0,"existing pending caused DB write");
  std::cout<<"CONTROL PASS: unresolved pending blocks new config candidate\n";
  return 0;
 } catch(const std::exception& e) { std::cerr<<e.what()<<"\n"; return 1; }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    args = parser.parse_args()
    host = (args.sources / 'order-service/Managers/Sdk/SdkSessionManager.cpp').read_text(encoding='utf-8')
    sdk = (args.sources / 'MAOrderSDK/src/connection/fix/FixEngine.cpp').read_text(encoding='utf-8')
    selected = [function(host, signature) for signature in [
        'void SdkSessionManager::seedFixPassword(',
        'std::optional<std::string> SdkSessionManager::armFromConfig(',
        'void SdkSessionManager::onFixPasswordChangeResult(',
        'void SdkSessionManager::onUserConnected(',
        'bool SdkSessionManager::FixPasswordPromoteNeeded(',
        'void SdkSessionManager::PromoteFixPasswordIfNeeded(',
    ]]
    selected.append(function(sdk, 'void FixEngine::fromAdmin('))
    for item in selected:
        print('SOURCE', item.split('(')[0].strip(), hashlib.sha256(item.encode()).hexdigest()[:16])
    vswhere = Path('C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe')
    installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
    if not installation:
        raise RuntimeError('MSVC Build Tools not found; no test executed')
    vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
    with tempfile.TemporaryDirectory(prefix='algo-password-check-') as temp:
        folder = Path(temp)
        (folder / 'check.cpp').write_text(ADAPTERS + '\n'.join(selected) + SCENARIOS, encoding='utf-8')
        command = 'call "' + str(vcvars) + '" >nul && cl /nologo /std:c++17 /EHsc /utf-8 check.cpp /Fe:check.exe'
        (folder / 'build.cmd').write_text('@echo off\n' + command + '\n', encoding='utf-8')
        built = subprocess.run(['cmd.exe', '/d', '/c', 'build.cmd'], cwd=folder, capture_output=True, text=True)
        if built.returncode:
            print(built.stdout, built.stderr)
            raise RuntimeError('C++ compilation failed; no scenario result')
        executed = subprocess.run([str(folder / 'check.exe')], cwd=folder, capture_output=True, text=True)
        print(executed.stdout)
        if executed.returncode:
            raise RuntimeError(executed.stderr or 'C++ scenario failed')
    print('PASS: 5 scenarios; production handler bodies, fake adapters; not QuickFIX integration')


if __name__ == '__main__':
    main()
