// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only observation of the pinned session, shared by private and public probes.
static void dump_spinner(const rich4::SpinnerState &s) {
    std::cout<<' '<<unsigned(s.type);for(auto v:s.digits)std::cout<<' '<<unsigned(v);
    std::cout<<' '<<unsigned(s.phase)<<' '<<unsigned(s.cursor)<<' '<<s.subject<<' '<<s.seed<<' '<<s.result;
}
static void dump_game_probe(rich4::GameSession::Impl &g,int status,
                           const std::vector<long long> &values,int successes=0,
                           bool finance=false,bool actors=false,
                           const std::vector<long long> &actor_values={}) {
            std::cout<<status<<' '<<g.random.state()<<' '<<int(g.phase)<<' '<<g.phase_elapsed<<' '<<g.pending_choice_key<<' '<<g.choice_sequence<<' '<<successes<<' '<<bool(g.pending_continuation);
            std::cout<<' '<<g.card_ai_memory.parameter0<<' '<<g.card_ai_memory.parameter1<<' '<<g.card_ai_memory.parameter2;
            for(auto v:g.costumes)std::cout<<' '<<unsigned(v);for(auto v:g.costume_keys)std::cout<<' '<<v;
            std::cout<<' '<<g.event_choices.size();for(auto [k,v]:g.event_choices)std::cout<<' '<<k<<' '<<v;
            std::cout<<' '<<g.choice_random_states.size();for(auto [k,v]:g.choice_random_states)std::cout<<' '<<k<<' '<<v;
            std::cout<<' '<<g.events.size();
            for(auto &e:g.events){std::cout<<' '<<int(e.kind)<<' '<<e.player<<' '<<e.amount<<' '<<e.node<<' '<<std::quoted(e.message)<<' '<<bool(e.voice_category);if(e.voice_category)std::cout<<' '<<unsigned(*e.voice_category);std::cout<<' '<<int(e.announcement)<<' '<<unsigned(e.announcement_id)<<' '<<e.property<<' '<<e.subject<<' '<<e.second_subject<<' '<<e.company<<' '<<e.value<<' '<<unsigned(e.players);for(auto v:e.player_amounts)std::cout<<' '<<v;std::cout<<' '<<bool(e.card);if(e.card)std::cout<<' '<<unsigned(*e.card);std::cout<<' '<<int(e.speech_table)<<' '<<unsigned(e.speech_slot)<<' '<<unsigned(e.speech_mood)<<' '<<bool(e.sound);if(e.sound)std::cout<<' '<<unsigned(*e.sound);}
            std::cout<<' '<<g.effects.size();for(auto &e:g.effects){std::cout<<' '<<int(e.kind)<<' '<<e.player<<' '<<e.node<<' '<<e.target.x<<' '<<e.target.y<<' '<<bool(e.from);if(e.from)std::cout<<' '<<e.from->x<<' '<<e.from->y;std::cout<<' '<<unsigned(e.object_kind)<<' '<<e.dice.size();for(auto v:e.dice)std::cout<<' '<<unsigned(v);std::cout<<' '<<e.property<<' '<<e.after_events<<' '<<bool(e.spinner)<<' '<<bool(e.monthly)<<' '<<unsigned(e.previous_level)<<' '<<unsigned(e.previous_type)<<' '<<unsigned(e.direction);if(e.spinner)dump_spinner(*e.spinner);
                if(e.monthly){auto &m=*e.monthly;std::cout<<' '<<unsigned(m.active);for(auto v:m.characters)std::cout<<' '<<unsigned(v);std::cout<<' '<<m.dividends.size();for(auto &row:m.dividends){std::cout<<' '<<unsigned(row.stock)<<' '<<row.earnings;for(auto v:row.payout)std::cout<<' '<<v;}for(auto v:m.tickets)std::cout<<' '<<unsigned(v);std::cout<<' '<<m.pool<<' '<<unsigned(m.number)<<' '<<m.winner;for(auto array:{m.cash,m.deposit,m.interest,m.balance,m.total})for(auto v:array)std::cout<<' '<<v;std::cout<<' '<<unsigned(m.loans);for(auto v:m.unlucky_days)std::cout<<' '<<unsigned(v);for(auto array:{m.income,m.spending})for(auto v:array)std::cout<<' '<<v;std::cout<<' '<<m.champion<<' '<<m.unlucky;}
            }
            std::cout<<' '<<bool(g.decision);if(g.decision){auto &d=*g.decision;std::cout<<' '<<int(d.kind)<<' '<<d.player<<' '<<d.land_id<<' '<<d.amount<<' '<<std::quoted(d.prompt)<<' '<<d.options.size();for(auto &o:d.options){std::cout<<' '<<std::quoted(o.label)<<' '<<o.value<<' '<<bool(o.location)<<' '<<bool(o.subject);if(o.location)std::cout<<' '<<o.location->x<<' '<<o.location->y;if(o.subject)std::cout<<' '<<int(o.subject->kind)<<' '<<o.subject->value;}std::cout<<' '<<d.max_amount<<' '<<bool(d.spinner)<<' '<<bool(d.mini_game)<<' '<<unsigned(d.inactive_players)<<' '<<bool(d.victim);if(d.spinner)dump_spinner(*d.spinner);if(d.mini_game)std::cout<<' '<<unsigned(d.mini_game->game)<<' '<<unsigned(d.mini_game->character)<<' '<<d.mini_game->seed;if(d.victim)std::cout<<' '<<*d.victim;}
            std::cout<<' '<<values.size();for(auto v:values)std::cout<<' '<<v;
            if(finance)std::cout<<' '<<(g.winner?int(*g.winner):-1)<<' '<<g.resume_movement<<' '<<g.bank_resume_encounter;
            if(actors){std::cout<<' '<<actor_values.size();for(auto v:actor_values)std::cout<<' '<<v;}
            std::cout<<'\n';
}
