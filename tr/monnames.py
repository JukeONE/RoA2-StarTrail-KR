import fill
N={'Ogre':'오거','Orc':'오크','Goblin':'고블린','Heshthot':'헤슈토트','Tusk Tiger':'엄니호랑이','Skeleton':'해골','Forest Gnome':'숲 노움','Mumm':'미라','Harp':'하피',
'Forest Spider':'숲거미','Stagga Beetle':'스타가 딱정벌레','Pirate':'해적','Navigator':'항해사','Captain':'선장','Rogue':'불량배','Zombie':'좀비','Druid':'드루이드',
'Thorwalian':'토르발인','Torturer':'고문 기술자','Dire Wol':'다이어울프','Cave Spider':'동굴거미','Warrior':'전사','Guardsm':'경비병','Magician':'마법사','Sorcerer':'흑마법사',
'Dwar':'드워프','Arkandor':'아르칸도르','Mammoth':'매머드','Cultist':'광신도','Priest':'사제','High Priest':'대사제','Estorik':'에스토릭','Pirate Captain':'해적 선장',
'Dwarven Veteran':'드워프 고참병','Robber':'강도','Gorah':'고라','Steppe Dog':'초원 들개','Forest Lion':'숲사자','Spider Demon':'거미 악마','Troll':'트롤','Ghoul':'구울',
'Zant':'찬트','Swamp Rantz':'늪 란치','Fire Spirit':'불의 정령','Praios Warrior':'프라이오스 전사','Merchant':'상인','Noblem':'귀족','Bandit Leader':'산적 두목',
'Guard Captain':'경비대장','Beggar':'거지','Orc Veteran':'오크 고참병','War Ogre':'전투 오거','Skeleton Warrior':'해골 전사','War Hound':'전투견','Gargoyle':'가고일',
'Golem':'골렘','Combat Magician':'전투 마법사','Knight':'기사','Bailiff':'포졸','Lion':'사자','Arkanian':'아르카니아인','Combat Dog':'투견','Wol':'늑대','El':'엘프',
'Elvish Veteran':'엘프 고참병','Engulfer':'삼킴괴물','Hunter':'사냥꾼','Witch':'마녀'}
import json
t=json.load(open('../text/MONNAMES.LTX.json',encoding='utf-8'))
T={}
for it in t['items']:
    en=it['en']; stem=en.split('.')[0]
    if en.startswith('Dwar.f (undead)'): T[it['id']]='드워프 언데드...'; continue
    if stem in N: T[it['id']]=N[stem]+'...'
    else: print('미번역',it['id'],en)
fill.fill('MONNAMES.LTX',T)
