// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only source extraction seam: unchanged draw_board construction prefix, actual original helpers/session.
#include "screens/main_screen.hpp"
#include "screens/effects.hpp"
#include "rich4/direction.hpp"
#include <iostream>
#include <sstream>
std::uint64_t test_ticks=0;
std::uint64_t SDL_GetTicks(){return test_ticks;}
using namespace rich4;
#include "main_scene_fixture.inc"
struct CaptureBoard {
    native::SceneData data;
    void render(graphics::Image &,const board::Scene &s,const board::Camera &){
        data.players.assign(s.players.begin(),s.players.end());data.objects.assign(s.objects.begin(),s.objects.end());
        data.lands.assign(s.lands.begin(),s.lands.end());data.facilities.assign(s.facilities.begin(),s.facilities.end());
        data.special_players.assign(s.special_players.begin(),s.special_players.end());data.commercials.assign(s.commercials.begin(),s.commercials.end());data.owners.assign(s.owners.begin(),s.owners.end());
    }
};
class Harness {
public:
    struct PresentationStep{std::optional<GameEvent> event;std::optional<EffectEvent> effect;};
    struct Focus{std::optional<std::size_t> slot;auto focus(){return slot;}} messages_;
    Harness(native::Artwork &art):effects_(art),board_(&capture){}
    std::unique_ptr<GameSession> session_;
    native::MainScreen main_screen_;
    native::EffectPlayer effects_;
    std::deque<PresentationStep> presentation_;
    std::optional<std::size_t> presented_player_;
    std::optional<board::Point> target_center_;
    unsigned rotation_=0;board::Camera current_camera_;CaptureBoard capture;CaptureBoard *board_;
    graphics::Image canvas_;bool busy=false;
    void sync_decision(){} // Decision synchronization is outside the extracted scene boundary.
    bool presenting(){return busy;}
#include "main_scene_source.inc"
};
int main(int argc,char **argv){
    if(argc!=2)return 2;
    try{
        native::Artwork art(argv[1]);std::string line;
        while(std::getline(std::cin,line)){
            std::istringstream in(line);unsigned map,v,elapsed,slot;std::uint64_t ticks;in>>map>>v>>elapsed>>ticks;slot=v%9;if(in>>slot){}
            Harness h(art);NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;
            h.session_=std::make_unique<GameSession>(World::from_map_resource(art.archive('m').decode(map*2+1),opt),1);
            auto &w=const_cast<World&>(h.session_->world());fixture(w,v);
            auto &animation=const_cast<std::optional<MoveAnimation>&>(h.session_->animation());animation=MoveAnimation{slot,int(100+v),100-int(v),67-int(v),int(132+v),elapsed,160};
            h.presented_player_=v%5?std::optional<std::size_t>(v%4):std::nullopt;h.busy=v&1;h.rotation_=v&7;
            if(v%3==0)h.main_screen_.free_scroll_=board::Point{400,500};
            if(v&2)const_cast<std::optional<GameDecision>&>(h.session_->pending_decision())=GameDecision{DecisionKind::card_target,0};
            if(v&4)h.target_center_=board::Point{700,800};
            if(v&8)h.messages_.slot=v%6;
            if(v&16){auto &s=h.main_screen_;s.dice_active_=true;s.dice_frames_=10;s.dice_elapsed_=elapsed;s.toss_slot_=v%4;s.toss_frames_=3;s.toss_ms_=240;}
            if(v%4){
                for(unsigned j=0;j<3;++j){EffectEvent e;e.kind=std::array{EffectKind::ambulance,EffectKind::parachute,EffectKind::object_throw}[j];e.player=(v+j)%4;e.from=EffectPoint{int(v*7+j),int(v*11+j)};e.object_kind=j==2?16:0;e.target={w.nodes[1].x,w.nodes[1].y};h.presentation_.push_back({std::nullopt,e});}
                const auto code=w.lands.size()>1?2001:4001;w.nodes[1].type_and_index=code;
                for(auto kind:{GameEventKind::land_purchased,GameEventKind::land_upgraded,GameEventKind::notice}){GameEvent e;e.kind=kind;e.player=0;e.node=1;if(kind==GameEventKind::notice)e.message="福神帮助房屋升级";h.presentation_.push_back({e,std::nullopt});}
            }
            if(v%7==0){EffectEvent e;e.kind=EffectKind::object_throw;e.object_kind=17;e.target={w.nodes[2].x,w.nodes[2].y};h.effects_.enqueue({e},h.session_.get());}
            const auto before=w.export_save();const auto rng=h.session_->random_state();test_ticks=ticks;h.draw_board();
            std::cout<<0;p(h.current_camera_.center.x);p(h.current_camera_.center.y);p(h.current_camera_.rotation);p(h.main_screen_.displayed_player_?static_cast<long long>(*h.main_screen_.displayed_player_):-1);
            scene(h.capture.data);p(h.effects_.pending_actors_.size());for(auto &x:h.effects_.pending_actors_){p(x.slot);p(bool(x.position));if(x.position){p(x.position->x);p(x.position->y);}p(x.injured);}
            p(before==w.export_save());p(rng==h.session_->random_state());std::cout<<'\n'<<std::flush;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
