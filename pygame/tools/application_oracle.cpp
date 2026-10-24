// SPDX-License-Identifier: GPL-3.0-or-later
// Test only: unedited original Application private draw/actions/observe/pump and real GameSession.
// Draw clock explicit; control dispatch and post-input tick sequence mirror the original run loop.
// Audio is explicitly disabled: waveforms and actual devices have their own direct oracles.
#define SDL_MAIN_HANDLED
#define SDL_GetTicks rich4_application_clock
#define main rich4_original_main
#include "native_game.cpp"
#undef main
#undef SDL_GetTicks
#include <type_traits>
static Uint64 app_ticks=0;
extern "C" Uint64 SDLCALL rich4_application_clock(){return app_ticks;}
int main(int argc,char **argv){
 if(argc!=7)return 2;
 std::ios::sync_with_stdio(false);std::cin.tie(nullptr);
 try{
  Options opt;opt.assets=argv[1];opt.font=argv[2];opt.save_directory=argv[3];opt.map=std::stoul(argv[4]);opt.seed=std::stoul(argv[5]);opt.auto_rounds=std::stoul(argv[6]);opt.headless=true;
  Application a(opt);a.audio_=std::make_unique<rich4::audio::Audio>(opt.assets,false);a.sound_effects_=false;
  const auto p=[](auto n){std::cout<<' '<<+n;};
  const auto text=[&](std::string_view s){std::uint64_t h=14695981039346656037ULL;for(unsigned char c:s)h=(h^c)*1099511628211ULL;p(s.size());p(h);};
  std::string line;
  while(std::getline(std::cin,line)){
   std::istringstream in(line);char op;in>>op;
   if(op=='D'){in>>app_ticks;a.draw();}
   else if(op=='I'){
    int id;in>>id;auto b=std::find_if(a.buttons_.begin(),a.buttons_.end(),[&](const auto &b){return b.id==id&&b.enabled;});if(b==a.buttons_.end())throw std::runtime_error("missing original enabled button "+std::to_string(id));
    const auto r=b->rectangle;auto action=b->action;a.frame_.pointer_x=(r.left+r.right)/2;a.frame_.pointer_y=(r.top+r.bottom)/2;a.frame_.pointer_down=true;
    if(id!=rich4::native::tile_popup::hit_id)a.tile_popup_.reset();a.buttons_.clear();action();a.frame_.pointer_down=false;
    if(a.screen_==Screen::game&&a.session_)a.main_screen_.pointer_up(a.frame_.pointer_x,a.frame_.pointer_y,false);
   }else if(op=='K'){
    int key;in>>key;if(key!=27)return 3;a.buttons_.clear();if(a.pad_.active())a.pad_key(SDLK_ESCAPE);else if(a.cancellable())a.cancel_screen();else a.screen_=a.screen_==Screen::game?Screen::menu:a.session_?Screen::game:Screen::menu;
   }else if(op=='U'){
    unsigned elapsed;in>>elapsed;
    if(a.session_&&a.screen_==Screen::game&&!a.items_.popup_active()&&!a.help_.active()){
     a.observe();a.hold_ms_-=std::min(a.hold_ms_,elapsed);
     if(!a.effects_.active()&&!a.messages_.active()&&!a.intro_.active())a.main_screen_.advance(elapsed);
     a.pump_presentation();if(a.presentation_.empty()&&!a.presenting()){
      a.effects_.remember(a.session_->world(),a.session_.get(),app_ticks);a.session_->tick(elapsed);
     }
     a.observe();if(a.session_->can_save()&&a.last_autosaved_day_!=a.session_->completed_days()){
      a.write_save(a.slot_path(0));a.last_autosaved_day_=a.session_->completed_days();
     }
    }
    a.update_board_audio();a.audio_->update();
   }else return 4;
   std::cout<<int(a.screen_);p(int(a.last_screen_));p(int(a.previous_screen_));p(a.rotation_);p(a.speed_);p(a.running_);p(a.sound_effects_);p(a.interactive_minigames_);p(a.selected_map_);p(a.selected_stage_);p(a.bank_amount_);p(a.selected_stock_);p(a.stock_card_hold_until_);p(a.stock_card_player_);p(a.humans_at_start_);p(a.cleared_maps_);p(a.cleared_stage_);p(a.last_autosaved_day_);text(a.toast_);p(a.toast_until_);text(a.decision_key_);text(a.voiced_decision_key_);p(a.decision_page_);
   p(bool(a.selected_target_));if(a.selected_target_)p(*a.selected_target_);p(bool(a.target_center_));if(a.target_center_){p(a.target_center_->x);p(a.target_center_->y);}
   p(a.hold_ms_);p(bool(a.presented_player_));if(a.presented_player_)p(*a.presented_player_);p(a.bankrupt_music_);p(a.auction_open_);
   p(a.presentation_.size());for(const auto &s:a.presentation_){p(bool(s.event));if(s.event){p(int(s.event->kind));p(s.event->player);p(s.event->amount);text(s.event->message);}p(bool(s.effect));if(s.effect){p(int(s.effect->kind));p(s.effect->player);p(s.effect->after_events);}}
   p(a.messages_.active());p(a.effects_.active());p(a.spinners_.active());p(a.monthly_.active());p(a.intro_.active());p(a.main_screen_.dice_busy());p(a.items_.popup_active());p(a.items_.magic_cast_active());p(a.auction_room_.sold_active());p(a.help_.active());p(a.pad_.active());
   p(a.frame_.pointer_x);p(a.frame_.pointer_y);p(a.frame_.pointer_down);p(a.frame_.ticks);p(a.buttons_.size());for(const auto &b:a.buttons_){p(b.id);p(b.rectangle.left);p(b.rectangle.top);p(b.rectangle.right);p(b.rectangle.bottom);p(b.enabled);p(b.click_sound);}
   p(a.event_counts_.size());for(const auto &[k,v]:a.event_counts_){p(int(k));p(v);}p(a.new_games_);p(a.loads_);p(a.saves_);p(a.rendered_frames_);p(bool(a.initial_random_state_));if(a.initial_random_state_)p(*a.initial_random_state_);
   p(a.audio_->music_enabled());p(a.audio_->music_track());p(a.audio_->music_context()?int(*a.audio_->music_context()):-1);p(a.audio_->music_depth());text(a.audio_->music_name());
   p(bool(a.session_));std::vector<std::uint8_t> world;if(a.session_){p(int(a.session_->phase()));p(a.session_->random_state());p(a.session_->completed_days());world=a.session_->world().export_save();p(bool(a.session_->pending_decision()));if(auto &d=a.session_->pending_decision()){p(int(d->kind));p(d->player);p(d->amount);p(d->max_amount);text(d->prompt);p(d->options.size());for(auto &o:d->options){text(o.label);p(o.value);p(bool(o.location));if(o.location){p(o.location->x);p(o.location->y);}p(bool(o.subject));if(o.subject){p(int(o.subject->kind));p(o.subject->value);}}}}
   p(op=='D'?a.canvas_.pixels.size()*2:0);p(world.size());std::cout<<'\n';
   if(op=='D')for(auto v:a.canvas_.pixels){std::cout.put(char(v));std::cout.put(char(v>>8));}std::cout.write(reinterpret_cast<const char *>(world.data()),world.size());std::cout.flush();
  }
 }catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}
}
