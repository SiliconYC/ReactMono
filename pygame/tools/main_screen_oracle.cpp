// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: fixed original MainScreen, real Python-independent C++ reference session and local pixels.
#include "screens/main_screen.hpp"
#include <iostream>
#include <sstream>
#include <memory>
int main(int argc,char **argv) {
    if(argc!=3)return 2;
    try {
        using namespace rich4;
        native::Artwork art(argv[1]);ui::Font font(argv[2]);
        auto canvas=graphics::make_canvas(640,480,0);
        std::vector<native::Button> buttons;native::Frame f(canvas,art,font,buttons);
        std::unique_ptr<GameSession> game;std::unique_ptr<native::MainScreen> screen;
        unsigned rotation=0;std::vector<int> calls,sounds;
        auto events=[&]{for(const auto &event:game->drain_events())screen->on_event(event,*game,art);};
        native::MainScreenActions actions;
        actions.help=[&]{calls.push_back(81);};actions.options=[&]{calls.push_back(76);};
        actions.ai=[&]{calls.push_back(82);};actions.load=[&]{calls.push_back(72);};
        actions.save=[&]{calls.push_back(71);};actions.query=[&]{calls.push_back(75);};
        actions.tools=[&]{calls.push_back(78);};actions.cards=[&]{calls.push_back(77);};
        actions.trading=[&]{calls.push_back(80);};actions.stocks=[&]{calls.push_back(79);};
        actions.rotate=[&](unsigned n){rotation=(rotation+n)&7;game->set_camera_rotation(rotation);calls.push_back(1000+n);};
        actions.roll=[&]{calls.push_back(100);calls.push_back(game->roll_dice());events();};
        actions.dice_count=[&](unsigned n){calls.push_back(101);calls.push_back(n);calls.push_back(game->set_dice_count(n));};
        actions.sound=[&](unsigned n){sounds.push_back(n);};
        unsigned step=0;std::string line;
        while(std::getline(std::cin,line)) {
            std::istringstream in(line);char op;in>>op;calls.clear();sounds.clear();int result=-1;
            if(op=='n') {
                unsigned map,seed,ch,traffic,year,month,day;std::string preset;
                in>>map>>seed>>ch>>traffic>>year>>month>>day>>preset;
                auto world=[&]{
                    if(map>=8)return World::from_save(SaveFile::decode(ui::read_file(ui::asset_path(argv[1],map==8?"Save0.dat":"SAVE1.DAT"))));
                    NewGameOptions opt;opt.map_id=map%4;opt.stage_id=map/4;opt.random_seed=seed;
                    opt.players[0].character=ch;opt.players[0].traffic_method=traffic;
                    opt.date={std::uint8_t(day),std::uint8_t(month),std::uint16_t(year)};
                    return World::from_map_resource(art.archive('m').decode(map*2+1),opt);
                }();
                game=std::make_unique<GameSession>(std::move(world),seed);
                screen=std::make_unique<native::MainScreen>(preset=="-"?"":preset);
                rotation=0;f.pointer_x=f.pointer_y=-1;f.pointer_down=false;f.ticks=0;events();
            }else if(!screen)return 3;
            else if(op=='d') {unsigned dt;in>>dt>>f.pointer_x>>f.pointer_y>>f.pointer_down;f.ticks+=dt;screen->advance(dt);}
            else if(op=='p') {
                in>>f.pointer_x>>f.pointer_y;f.pointer_down=true;
                for(auto &b:buttons)if(b.enabled&&ui::contains(b.rectangle,f.pointer_x,f.pointer_y)) {
                    auto action=b.action;calls.push_back(b.id);buttons.clear();action();break;
                }
            }else if(op=='m'){int x,y;bool down;in>>x>>y>>down;f.pointer_x=x;f.pointer_y=y;f.pointer_down=down;screen->pointer_motion(x,y,down);}
            else if(op=='u'){int x,y;bool right;in>>x>>y>>right;f.pointer_x=x;f.pointer_y=y;f.pointer_down=false;screen->pointer_up(x,y,right);}
            else if(op=='s'){int slot;in>>slot;screen->set_displayed_player(slot<0?std::nullopt:std::optional<std::size_t>(slot));}
            else if(op=='v')screen->cycle_view_mode();
            else if(op=='h'){bool skip;in>>skip;screen->set_skip_toss(skip);}
            else if(op=='g'){int x,y;in>>x>>y;result=screen->go_mask(f,x,y);}
            else if(op=='r'){result=game->roll_dice();events();}
            else if(op=='c'){unsigned dt;in>>dt;result=!screen->dice_busy();if(result){game->tick(dt);events();}}
            else if(op=='a'){in>>actions.can_save>>actions.can_load;}
            else return 4;
            for(std::size_t i=0;i<canvas.pixels.size();++i)canvas.pixels[i]=(i*1103515245ULL+step)&65535;
            buttons.clear();screen->draw(f,*game,rotation,actions);
            std::cout<<result;auto p=[&](auto n){std::cout<<' '<<static_cast<long long>(n);};
            p(game->phase());p(game->world().header.current_player);p(rotation);p(f.ticks);
            p(screen->dice_busy());p(screen->human_turn_shown(*game));p(screen->displayed_player(game->world()));
            p(screen->view_mode_);p(screen->calendar_mode_);for(auto x:screen->tab_)p(x);p(screen->hover_);p(screen->go_x_);p(screen->go_y_);
            p(bool(screen->go_drag_));if(screen->go_drag_){p(screen->go_drag_->first);p(screen->go_drag_->second);}
            p(screen->displayed_player_?static_cast<long long>(*screen->displayed_player_):-1);p(bool(screen->pending_roll_));p(screen->press_point_.first);p(screen->press_point_.second);
            p(bool(screen->free_scroll_));if(screen->free_scroll_){p(screen->free_scroll_->x);p(screen->free_scroll_->y);}
            p(screen->minimap_drag_);p(screen->full_map_);p(screen->minimap_top_);p(screen->go_mask_.size());
            p(screen->dice_faces_.size());for(auto x:screen->dice_faces_)p(x);p(screen->dice_direction_);
            p(screen->dice_active_);p(screen->dice_sound_played_);p(screen->skip_toss_);p(screen->dice_elapsed_);p(screen->dice_frames_);p(screen->toss_slot_);p(screen->toss_frames_);p(screen->toss_ms_);
            p(screen->dice_animations_.size());for(auto &[n,v]:screen->dice_animations_){p(n);p(v.size());}
            for(std::size_t slot=0;slot<4;++slot){auto pose=screen->toss_frame(slot);p(pose?*pose:-1);}
            p(buttons.size());for(auto &b:buttons){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
            p(calls.size());for(auto x:calls)p(x);p(sounds.size());for(auto x:sounds)p(x);std::cout<<'\n';
            for(auto v:canvas.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.flush();++step;
        }
    }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
