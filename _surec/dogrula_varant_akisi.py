"""Source-extracted Varant handlers; fake SDK, real std::mutex, MSVC only.

No exchange, source writes or full application integration. A child-process
watchdog bounds the intentionally blocked synchronous rejection scenario.
"""
import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path
from dogrula_sifre_akisi import function

ADAPTERS = r'''
#include <string>
#include <vector>
#include <map>
#include <mutex>
#include <atomic>
#include <algorithm>
#include <functional>
#include <iostream>
#include <stdexcept>
#define LOG_INFO(...) ((void)0)
#define LOG_WARN(...) ((void)0)
namespace ouchSDK {
 namespace enums {enum class Side{BUY,SELL}; enum class TimeInForce{TIF_IMMEDIATE_OR_CANCEL}; enum class OrdType{REGULAR_ORDER_LIMIT};}
 namespace models {struct StrategyInfo {template<class... T> StrategyInfo(T...){} int getStrategyType(){return 13;} int getOverallValue(){return 0;}};}
}
namespace hft {namespace enums {namespace strategy {enum class MessageType{Warrant,UserOrder};}}}
namespace Hft {
 struct EnterOrder {template<class... T> EnterOrder(T...){} void setParentOrderbookId(uint32_t){} };
 struct Token {std::string value; std::string getOrderToken()const{return value;}};
 struct ReplaceOrder {Token sdkReplaceOrder; uint64_t quantity; ReplaceOrder(std::string t,uint32_t,uint64_t q):sdkReplaceOrder{t},quantity(q){} };
 struct Accepted {std::string token; uint64_t instrument; ouchSDK::enums::Side side;
  std::string getOrderToken(){return token;} uint64_t getOrderbookId(){return instrument;} auto getSide(){return side;}};
 struct OrderAccepted {Accepted sdkOrderAccepted; auto getCustomerInfo(){return hft::enums::strategy::MessageType::Warrant;}};
 struct OrderRejected {Token sdkOrderRejected;};
}
struct HftConvert {static Hft::EnterOrder toSdkMsg(Hft::EnterOrder o,std::string,std::string){return o;}
 static Hft::ReplaceOrder toSdkMsg(Hft::ReplaceOrder o,std::string){return o;}};
struct UtilityClass {static std::string generateToken(){return "new";}};
struct OuchManager {static OuchManager& instance(){static OuchManager o;return o;}
 std::string getNewFatherOrderRef(){return "father";} void enterOrder(Hft::EnterOrder,std::string,std::string){} void replaceOrder(Hft::ReplaceOrder){} };
struct StrategyManager {static StrategyManager& instance(){static StrategyManager s;return s;} void markStrategyDirty(std::string){} };
struct FakeSDK {std::function<void()> callback; int replaces=0; std::string token; uint64_t quantity=0;
 bool enterOrder(Hft::EnterOrder){if(callback)callback();return false;} bool ownsAccount(std::string){return true;}
 bool replaceOrder(Hft::ReplaceOrder o){++replaces;token=o.sdkReplaceOrder.value;quantity=o.quantity;return true;}
 bool ownsOrder(std::string){return true;}};
struct HftWarrant {
 enum class DerivativeState{Idle,BuyOrderPending,BuyOrderPartiallyFilled,BuyOrderFilled,SellOrderPending,SellOrderPartiallyFilled,SellOrderFilled,OrdersCancelled,Error};
 enum class StrategyState{Idle,BuyOrdersActive,SellOrdersActive};
 struct DerivativeInstrument {uint64_t instrumentId=1; std::string symbol="fake"; double userPrice=1; uint64_t userQuantity=60; bool isActive=true;
  std::string activeOrderToken; bool hasPendingSell=false; std::string sellOrderToken; DerivativeState currentState=DerivativeState::Idle;
  uint64_t buyFilledQuantity=0,sellFilledQuantity=0; bool isReplacedToTarget=false;};
 std::mutex derivativeMutex; std::vector<DerivativeInstrument> derivativeInstruments{DerivativeInstrument{}};
 std::atomic<StrategyState> strategyState{StrategyState::Idle}; std::map<std::string,Hft::OrderAccepted*> orderMap;
 FakeSDK* maosdk=nullptr; std::string account="fake"; uint64_t underlyingInstrumentId=2; ouchSDK::models::StrategyInfo strategyInfo{0};
 std::string getAccount(){return account;} std::string getStrategyIdentifier(){return "fake";} std::string getUniqueKey(){return "fake";}
 void executeBuyOrders(); void rejectOrder(Hft::OrderRejected*); void addOrder(Hft::OrderAccepted*); void replaceToTarget(const DerivativeInstrument&);
};
void require(bool v,const char* m){if(!v)throw std::runtime_error(m);}
'''

SCENARIOS = r'''
int main(int argc,char** argv){try{
 std::string mode=argc>1?argv[1]:"tokens";
 HftWarrant host; FakeSDK sdk;host.maosdk=&sdk;
 if(mode!="tokens"){
  Hft::OrderRejected rejected{{"rejected"}};
  sdk.callback=[&]{std::cout<<"ENTER_REJECT\n"<<std::flush;host.rejectOrder(&rejected);std::cout<<"RETURN_REJECT\n"<<std::flush;};
  if(mode=="locked"){std::lock_guard<std::mutex> held(host.derivativeMutex);host.executeBuyOrders();}
  else host.executeBuyOrders();
  std::cout<<"RETURN_SEND\n";return 0;
 }
 Hft::OrderAccepted first{{"S1",1,ouchSDK::enums::Side::SELL}},second{{"S2",1,ouchSDK::enums::Side::SELL}};
 host.derivativeInstruments[0].buyFilledQuantity=60;
 host.addOrder(&first);host.addOrder(&second);
 require(host.orderMap.size()==2,"two accepts not retained in map");
 host.replaceToTarget(host.derivativeInstruments[0]);
 require(sdk.replaces==1&&sdk.token=="S2"&&sdk.quantity==60,"K242 observation changed; review source");
 require(host.orderMap.count("S1")==1,"first accept disappeared");
 std::cout<<"OBSERVED K242: S1 and S2 accepted; only S2 replaced with aggregate 60\n";
 host.replaceToTarget(host.derivativeInstruments[0]);require(sdk.replaces==1,"repeat replace not suppressed");
 std::cout<<"CONTROL PASS: repeated target replace suppressed\n";
 HftWarrant single;FakeSDK one;single.maosdk=&one;single.derivativeInstruments[0].buyFilledQuantity=60;
 single.addOrder(&first);single.replaceToTarget(single.derivativeInstruments[0]);
 require(one.replaces==1&&one.token=="S1"&&one.quantity==60,"single-sale control failed");
 std::cout<<"CONTROL PASS: single sale uses S1 with 60\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    args = parser.parse_args()
    source = (args.sources / 'HftSrvProd/src/Strategy/HftWarrant.cpp').read_text(encoding='utf-8')
    selected = [function(source, 'void HftWarrant::' + name + '(')
                for name in ['executeBuyOrders', 'rejectOrder', 'addOrder', 'replaceToTarget']]
    caller = function(source, 'void HftWarrant::processItchEventTimed(')
    # Fail if the source boundary used by the locked caller fixture changes.
    if not ('std::lock_guard<std::mutex> lock(derivativeMutex);' in caller
            and caller.index('lock(derivativeMutex)') < caller.index('executeBuyOrders();')):
        raise RuntimeError('Caller lock boundary changed; review fixture')
    for item in selected:
        print('SOURCE', item.split('(')[0], hashlib.sha256(item.encode()).hexdigest()[:16])
    vswhere = Path('C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe')
    installation = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
    if not installation:
        raise RuntimeError('MSVC unavailable; no scenarios executed')
    vcvars = Path(installation) / 'VC/Auxiliary/Build/vcvars64.bat'
    with tempfile.TemporaryDirectory(prefix='algo-warrant-check-') as temp:
        folder = Path(temp)
        (folder / 'check.cpp').write_text(ADAPTERS + '\n'.join(selected) + SCENARIOS, encoding='utf-8')
        (folder / 'build.cmd').write_text('@echo off\ncall "' + str(vcvars) +
            '" >nul && cl /nologo /std:c++17 /EHsc /utf-8 check.cpp /Fe:check.exe\n', encoding='utf-8')
        built = subprocess.run(['cmd.exe', '/d', '/c', 'build.cmd'], cwd=folder, capture_output=True, text=True)
        if built.returncode:
            raise RuntimeError(built.stdout + built.stderr)
        for mode in ['unlocked', 'tokens']:
            ran = subprocess.run([str(folder / 'check.exe'), mode], capture_output=True, text=True, timeout=5)
            print(ran.stdout)
            if ran.returncode or (mode == 'unlocked' and 'RETURN_SEND' not in ran.stdout):
                raise RuntimeError(ran.stderr or 'Control failed')
        try:
            ran = subprocess.run([str(folder / 'check.exe'), 'locked'], capture_output=True, timeout=3)
        except subprocess.TimeoutExpired as stalled:
            output = stalled.stdout or b''
            if b'ENTER_REJECT' not in output or b'RETURN_REJECT' in output:
                raise RuntimeError('Unexpected watchdog boundary')
            print('OBSERVED K241: synchronous reject entered; no return within 3s while caller holds mutex')
        else:
            if (ran.returncode != 1 or b'ENTER_REJECT' not in ran.stdout
                    or b'RETURN_REJECT' in ran.stdout or b'resource deadlock would occur' not in ran.stderr):
                raise RuntimeError('Unexpected locked scenario result: ' + repr(ran))
            print('OBSERVED K241: MSVC throws resource deadlock would occur at recursive mutex acquisition')
    print('PASS: 5 scenarios; fake SDK/caller boundary, actual handler bodies; no exchange integration')


if __name__ == '__main__':
    main()
