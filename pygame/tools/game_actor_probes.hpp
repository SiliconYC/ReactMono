// SPDX-License-Identifier: GPL-3.0-or-later
// Test-only dispatch to the pinned Impl; the game runtime never includes this adapter.
static void actor_probe(rich4::GameSession::Impl &g, const std::vector<long long> &n,
                        std::vector<long long> &v) {
    switch(n.at(0)) {
    case 0:g.sync_attached_objects(n.at(1));break;
    case 1:g.clear_absences(n.at(1));break;
    case 2:g.relocate_bankrupt(n.at(1));break;
    case 3:g.injure(n.at(1));break;
    case 4:g.add_confinement(n.at(1),n.at(2),n.at(3));break;
    case 5:g.disappear(n.at(1),n.at(2),n.at(3));break;
    case 6:v={g.try_free_card(n.at(1),n.at(2),n.at(3))};break;
    case 7:v={g.try_frame_card(n.at(1),n.at(2),n.at(3))};break;
    case 8:v={g.try_defense_card(n.at(1))};break;
    case 9:v={g.choose_victim_card(n.at(1),n.at(2))};break;
    case 10:g.release_hotel_guests();break;
    case 11:g.change_building(n.at(1),n.at(2));break;
    case 12:g.construction_vehicle_demolish();break;
    case 13:g.turn_around(n.at(1));break;
    case 14:{auto r=g.auction(n.at(1),n.at(2));v={r.winner?int(*r.winner):-1,r.price,r.property};break;}
    case 15:v={g.random_free_node(n.at(1))};break;
    case 16:g.place_existing_object(n.at(1),n.at(2));break;
    case 17:g.remove_object(n.at(1));break;
    case 18:{std::int32_t amount=n.at(1);auto payer=g.select_toll_payer(amount,n.at(2),n.at(3),n.at(4));v={static_cast<long long>(payer),amount};break;}
    default:throw std::invalid_argument("actor probe");
    }
}

static bool actor_prepare(rich4::GameSession::Impl &g, char op, const std::vector<long long> &n) {
    if(op=='U') {
        auto &p=g.world.players.at(n.at(0));auto &s=p.state;auto &t=p.status;
        s.node_id=n.at(1);s.last_node_id=n.at(2);s.traffic_method=n.at(3);s.dice_count=n.at(4);s.controller_flags=n.at(5);
        t.days_in_hotel=n.at(6);t.days_disappearing=n.at(7);t.days_in_prison=n.at(8);t.days_in_hospital=n.at(9);t.days_sleeping=n.at(10);t.days_sleep_walking=n.at(11);t.god_info=n.at(12);t.attached_bomb=n.at(13);t.saved_direction=n.at(14);
        t.god_luck_modifier=n.at(15);t.money_fortune_modifier=n.at(16);t.other_fortune_modifier=n.at(17);
    }else if(op=='O') {
        auto &p=g.world.objects.at(n.at(0));p.kind=n.at(1);p.node_id=n.at(2);p.remaining_days=n.at(3);p.attached_player=n.at(4);p.direction=n.at(5);
    }else if(op=='V') {
        auto &p=g.world.players.at(n.at(0)).state;for(unsigned i=0;i<15;++i)p.cards[i]=n.at(i+1);
    }else if(op=='E') {
        auto code=n.at(0);if(code>=4000){auto &p=g.world.facilities.at(code-4000);p.owner_code=n.at(1);p.level=n.at(2);p.facility_type=n.at(3);p.temporary_state=n.at(4);p.expired_date=n.at(5);}else{auto &p=g.world.lands.at(code-2000);p.economy.owner_code=n.at(1);p.economy.level=n.at(2);p.economy.chain_store=n.at(3);p.temporary_state=n.at(4);p.expired_date=n.at(5);}
    }else if(op=='R') {
        auto &p=g.world.special_actors.at(n.at(0));p.node_id=n.at(1);p.last_node_id=n.at(2);p.owner=n.at(3);p.inactive_state=n.at(4);p.flags=n.at(5);p.days_sleeping=n.at(6);p.days_sleep_walking=n.at(7);p.days_stopping=n.at(8);p.days_tortoise_walking=n.at(9);
    }else return false;
    return true;
}
