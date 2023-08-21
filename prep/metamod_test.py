#!/usr/bin/env python

import textwrap

import pytest
from metamod import *

""" Globals """
test_libraries = {}
test_blocks = {}


""" Spell """


def test_spell_darkness_name():
    s = Spell(block=test_blocks['darkness'])
    assert s.name == 'Target_Darkness'


def test_spell_darkness_type():
    s = Spell(block=test_blocks['darkness'])
    assert s.type == 'Target'


def test_darkness_data_icon():
    s = Spell(block=test_blocks['darkness'])
    assert s.data['Icon'] == 'Spell_Evocation_Darkness'


def test_spell_darkness_is_concentration():
    s = Spell(block=test_blocks['darkness'])
    assert 'IsConcentration' in s.flags


def test_spell_darkness_with_bogus_flag():
    s = Spell(block=test_blocks['darkness'])
    assert not 'BogusFlag' in s.flags


def test_spell_darkness_not_container():
    s = Spell(block=test_blocks['darkness'])
    assert s.has_no_container_spells()


def test_spell_darkness_3_not_container():
    s = Spell(block=test_blocks['darkness_3'])
    assert s.has_no_container_spells()


def test_spell_darkness_3_has_root_spell():
    s = Spell(block=test_blocks['darkness_3'])
    assert s.has_root_spell()


def test_spell_darkness_3_has_no_spellcontainer():
    s = Spell(block=test_blocks['darkness_3'])
    assert not s.has_spell_container()


def test_spell_empty():
    with pytest.raises(SpellParseException) as e:
        s = Spell(block="")
    assert 'too few lines' in str(e.value)


def test_spell_malformatted_header():
    with pytest.raises(SpellParseException) as e:
        block = textwrap.dedent("""\
            new entry "Test_Spell"\
            type "Bogus"
            data "SpellType" "Test"
        """)
        s = Spell(block=block)
    assert 'missing type field' in str(e.value)


def test_spell_malformatted_type():
    with pytest.raises(SpellParseException) as e:
        block = textwrap.dedent("""\
            new entry "Test_Spell"\
            type "SpellData"
            data "HAHA"
        """)
        s = Spell(block=block)
    assert 'missing type field' in str(e.value)


def test_spell_hex_is_container():
    s = Spell(block=test_blocks['hex'])
    assert s.has_container_spells()


def test_spell_hex_has_linked_container_flag():
    s = Spell(block=test_blocks['hex'])
    assert 'IsLinkedSpellContainer' in s.flags


def test_spell_with_spell_container_id():
    s = Spell(block=test_blocks['spell_container_id'])
    assert s.has_spell_container()


def test_spell_with_spell_container_id():
    s = Spell(block=test_blocks['spell_container_id'])
    assert s.spell_container_id == "Projectile_EnsnaringStrike_Container"


def test_spell_with_no_spell_container_id():
    s = Spell(block=test_blocks['no_spell_container_id'])
    assert not s.has_spell_container()


def test_spell_with_empty_spell_container_id():
    s = Spell(block=test_blocks['no_spell_container_id'])
    assert s.spell_container_id == ""


def test_spell_containerize():
    s = Spell(block=test_blocks['darkness'])
    s.containerize()
    assert 'IsLinkedSpellContainer' in s.flags


def test_spell_decontainerize():
    s = Spell(block=test_blocks['hex'])
    s.decontainerize()
    assert s.data['ContainerSpells'] == '' and 'IsLinkedSpellContainer' not in s.flags


def test_spell_duplicate():
    s = Spell(block=test_blocks['darkness'])
    s2 = s.duplicate('Target_Darkness_Clone')
    assert s.name != s2.name and s.type == s2.type


def test_spell_duplicate_and_decontainerize():
    s = Spell(block=test_blocks['darkness'])
    s2 = s.duplicate('Target_Darkness_Clone')
    s2.decontainerize()
    assert 'IsLinkedSpellContainer' not in s2.flags


def test_spell_create_meta_will_decontainerize():
    s = Spell(block=test_blocks['darkness'])
    s2 = s.create_meta(postfix='Clone')
    assert 'IsLinkedSpellContainer' not in s2.flags


def test_spell_firebolt_swap_element():
    s = Spell(block=test_blocks['firebolt'])
    s.swap_element('Cold')
    assert s.damage_type == 'Cold'


def test_spell_duplicate_firebolt_swap_element():
    s = Spell(block=test_blocks['firebolt'])
    s2 = s.duplicate('Projectile_FireBolt_Test')
    s2.swap_element('Cold')
    assert s2.damage_type == 'Cold'


def test_spell_create_meta_firebolt_swap_element():
    s = Spell(block=test_blocks['firebolt'])
    s2 = s.create_meta(postfix='Test')
    s2.swap_element('Cold')
    assert s2.damage_type == 'Cold'


def test_spell_create_meta_darkness_container():
    s = Spell(block=test_blocks['darkness'])
    s2 = s.create_meta(postfix='Test')
    assert s2.spell_container_id == 'Target_Darkness'


def test_spell_create_meta_darkness_3_container():
    s = Spell(block=test_blocks['darkness_3'])
    s2 = s.create_meta(postfix='Test')
    assert s2.spell_container_id == 'Target_Darkness_3'


def test_spell_create_meta_darkness_3_root_spell():
    s = Spell(block=test_blocks['darkness_3'])
    s2 = s.create_meta(postfix='Test')
    assert s2.root_spell_id == 'Target_Darkness_Test'


def test_spell_create_meta_darkness_3_deprioritized_root_spell():
    s = Spell(block=test_blocks['darkness_3'])
    s2 = s.create_meta(postfix='Test', deprioritized=True)
    assert s2.root_spell_id == '_Target_Darkness_Test'


def test_spell_create_meta_scorchingray_container():
    s = Spell(block=test_blocks['scorchingray'])
    s2 = s.create_meta(postfix='Test')
    assert s2.spell_container_id == 'Projectile_ScorchingRay'


def test_spell_create_meta_scorchingray_3_container():
    s = Spell(block=test_blocks['scorchingray_3'])
    s2 = s.create_meta(postfix='Test')
    assert s2.spell_container_id == 'Projectile_ScorchingRay_3'


def test_spell_create_meta_scorchingray_3_root_spell():
    s = Spell(block=test_blocks['scorchingray_3'])
    s2 = s.create_meta(postfix='Test')
    assert s2.root_spell_id == 'Projectile_ScorchingRay_Test'


def test_spell_create_meta_scorchingray_3_deprioritized_root_spell():
    s = Spell(block=test_blocks['scorchingray_3'])
    s2 = s.create_meta(postfix='Test', deprioritized=True)
    assert s2.root_spell_id == '_Projectile_ScorchingRay_Test'


def test_spell_top_original_has_no_root_spell():
    s = Spell(block=test_blocks['scorchingray'])
    s_list = s.create_originals(postfix='Original')
    for spell in s_list:
        assert not spell.root_spell_id


def test_spell_leveled_original_has_root_spell():
    s = Spell(block=test_blocks['scorchingray_3'])
    s_list = s.create_originals(postfix='Original')
    for spell in s_list:
        if spell.is_leveled():
            print(spell.to_text())
            assert spell.root_spell_id == 'Projectile_ScorchingRay_Original'


""" SpellLibrary """

# def test_spell_library_load_non_existent():
#     with pytest.raises(FileNotFoundError) as e:
#         SpellLibrary('path/to/bogus')
#     assert 'file not found' in str(e.value)


def test_spell_library_load_hex():
    sl = test_libraries['hex']
    assert len(sl.spell_map) == 35


def test_spell_library_load_enlarge_reduce():
    sl = test_libraries['enlarge_reduce']
    assert len(sl.spell_map) == 12


def test_spell_library_hex_spell_available():
    sl = test_libraries['hex']
    assert sl.spell_map.get('Target_Hex', None)


def test_spell_library_hex_strength_spell_available():
    sl = test_libraries['hex']
    assert sl.spell_map.get('Target_Hex_Strength', None)


def test_spell_library_hex_2_spell_available():
    sl = test_libraries['hex']
    assert sl.spell_map.get('Target_Hex_2', None)


def test_spell_library_hex_2_has_root_spell():
    sl = test_libraries['hex']
    s = sl.spell_map['Target_Hex_2']
    assert s.has_root_spell()


def test_spell_library_hex_2_has_container_spells():
    sl = test_libraries['hex']
    s = sl.spell_map['Target_Hex_2']
    assert s.has_container_spells()


def test_spell_library_hex_2_has_usage():
    sl = test_libraries['hex']
    s = sl.spell_map['Target_Hex_2']
    assert s.has_using()


def test_spell_library_hex_has_child_strength():
    sl = test_libraries['hex']
    parent = sl.spell_map['Target_Hex']
    child = sl.spell_map['Target_Hex_Strength']
    assert child in parent.children


def test_spell_library_hex_2_has_parent_hex():
    sl = test_libraries['hex']
    child = sl.spell_map['Target_Hex_2']
    parent = sl.spell_map['Target_Hex']
    assert child.parent == parent


def test_spell_library_self_using_exception():
    with pytest.raises(SpellLinkException) as e:
        f = "testdata/bugs/Spell_SacredFlame_self_using.txt"
        SpellLibrary(SpellFilterOptions(path=f))
    assert 'is referencing itself for inheritance' in str(e.value)


def test_spell_library_hex_has_member_strength():
    sl = test_libraries['hex']
    container = sl.spell_map['Target_Hex']
    member = sl.spell_map['Target_Hex_Strength']
    assert member in container.members


def test_spell_library_hex_strength_has_container_hex():
    sl = test_libraries['hex']
    container = sl.spell_map['Target_Hex']
    member = sl.spell_map['Target_Hex_Strength']
    assert member.container.name == container.name


def test_spell_library_hex_strength_2_has_container_hex_2():
    sl = test_libraries['hex']
    container = sl.spell_map['Target_Hex_2']
    member = sl.spell_map['Target_Hex_Strength_2']
    assert member.container == container


def test_self_containerization_exception():
    with pytest.raises(SpellLinkException) as e:
        f = "testdata/bugs/Spell_Darkness_self_container.txt"
        SpellLibrary(SpellFilterOptions(path=f))
    assert 'is referencing itself for containerization' in str(e.value)


"""" Setup test cases """


def setup_module(module):
    global test_libraries, test_spells

    libraries = {
        'enlarge_reduce': 'testdata/enlarge_reduce/*.txt',
        'hex': 'testdata/hex/*.txt',
    }
    for spell_family, path in libraries.items():
        sl = SpellLibrary(SpellFilterOptions(path=path))
        test_libraries[spell_family] = sl

    blocks = {
        'darkness': textwrap.dedent("""\
            new entry "Target_Darkness"
            type "SpellData"
            data "SpellType" "Target"
            data "Level" "2"
            data "SpellSchool" "Evocation"
            data "SpellProperties" "GROUND:CreateSurface(5,10,DarknessCloud,true)"
            data "TargetRadius" "18"
            data "AreaRadius" "5"
            data "Icon" "Spell_Evocation_Darkness"
            data "DisplayName" "h0ea62574g0e90g491bg8054g78bf8c61ac45;1"
            data "Description" "h64652503g229ag4f9ag819cg8d9411c66209;4"
            data "TooltipUpcastDescription" "6ff1780a-855a-414c-a8bf-811251537206"
            data "CastSound" "Spell_Cast_Utility_Darkness_L1to3"
            data "TargetSound" "Spell_Impact_Utility_Darkness_L1to3"
            data "VocalComponentSound" "Vocal_Component_Dark"
            data "CastTextEvent" "Cast"
            data "CycleConditions" "Enemy() and not Dead()"
            data "UseCosts" "ActionPoint:1;SpellSlotsGroup:1:1:2"
            data "SpellAnimation" "dd86aa43-8189-4d9f-9a5c-454b5fe4a197,,;,,;7abe77ed-9c77-4eac-872c-5b8caed070b6,,;cb171bda-f065-4520-b470-e447f678ba1f,,;cc5b0caf-3ed1-4711-a50d-11dc3f1fdc6a,,;,,;1715b877-4512-472e-9bd0-fd568a112e90,,;bcc3b0d9-f04f-4448-aab0-e0ad641167cc,,;bf924cc6-8b39-4c3b-b1c0-eda264cf6150,,"
            data "VerbalIntent" "Utility"
            data "SpellFlags" "HasVerbalComponent;IsSpell;IsConcentration;Stealth;Invisible"
            data "MemoryCost" "1"
            data "PrepareEffect" "7121a488-7c9a-4ba1-a585-f79aaa77e97c"
            data "CastEffect" "e61d2266-f041-4bd5-a488-7b66e76d781c"
            data "PositionEffect" "0afcbe13-7593-4bb7-8dfd-b7147a3f416c"\
        """),

        'darkness_3': textwrap.dedent("""\
            new entry "Target_Darkness_3"
            type "SpellData"
            data "SpellType" "Target"
            using "Target_Darkness"
            data "UseCosts" "ActionPoint:1;SpellSlotsGroup:1:1:3"
            data "RootSpellID" "Target_Darkness"
            data "PowerLevel" "3"\
        """),

        'firebolt': textwrap.dedent("""\
            new entry "Projectile_FireBolt"
            type "SpellData"
            data "SpellType" "Projectile"
            data "Level" "0"
            data "SpellSchool" "Evocation"
            data "SpellProperties" "GROUND:SurfaceChange(Ignite);GROUND:SurfaceChange(Melt)"
            data "TargetFloor" "-1"
            data "TargetRadius" "18"
            data "SpellRoll" "Attack(AttackType.RangedSpellAttack)"
            data "SpellSuccess" "DealDamage(LevelMapValue(D10Cantrip),Fire,Magical)"
            data "TargetConditions" "not Self() and not Dead()"
            data "ProjectileCount" "1"
            data "Trajectories" "792ba497-a6ea-46bc-81cb-deb78e4dd9d3"
            data "Icon" "Spell_Evocation_FireBolt"
            data "DisplayName" "h7fddad46g70f6g4c7dg8109gab93722b0495;1"
            data "Description" "h111ae255g55f1g4a55gb958g517af226971b;4"
            data "TooltipDamageList" "DealDamage(LevelMapValue(D10Cantrip),Fire)"
            data "TooltipAttackSave" "RangedSpellAttack"
            data "PrepareSound" "Spell_Prepare_Damage_Fire_Gen_L1to3"
            data "PrepareLoopSound" "Spell_Prepare_Damage_Fire_Gen_L1to3_Loop"
            data "CastSound" "Spell_Cast_Damage_Fire_FireBolt_L1to3"
            data "PreviewCursor" "Cast"
            data "CastTextEvent" "Cast"
            data "CycleConditions" "Enemy() and not Dead()"
            data "UseCosts" "ActionPoint:1"
            data "SpellAnimation" "3ff87abf-1ea1-4c32-aadf-c822d74c7dc0,,;,,;38cdb41c-2eec-4e03-bb31-83cff0346c35,,;85414f5f-b448-4dda-9370-1b6c4b38b561,,;d8925ce4-d6d9-400c-92f5-ad772ef7f178,,;,,;eadedcce-d01b-4fbb-a1ae-d218f13aa5d6,,;,,;,,"
            data "VerbalIntent" "Damage"
            data "SpellFlags" "HasVerbalComponent;HasSomaticComponent;IsSpell;HasHighGroundRangeExtension;RangeIgnoreVerticalThreshold;IsHarmful"
            data "HitAnimationType" "MagicalDamage_External"
            data "PrepareEffect" "c88e9cfa-df92-477a-ae75-cbfb932350b4"
            data "CastEffect" "e235ca47-1bf5-4587-9475-cf191b6005f9"
            data "DamageType" "Fire"\
        """),

        'hex': textwrap.dedent("""\
            new entry "Target_Hex"
            type "SpellData"
            data "SpellType" "Target"
            data "Level" "1"
            data "SpellSchool" "Enchantment"
            data "ContainerSpells" "Target_Hex_Strength;Target_Hex_Dexterity;Target_Hex_Constitution;Target_Hex_Intelligence;Target_Hex_Wisdom;Target_Hex_Charisma"
            data "TargetRadius" "18"
            data "TargetConditions" "Character()"
            data "Icon" "Spell_Enchantment_Hex"
            data "DisplayName" "heb47bc26gcd09g429cg97f6g21791a883edf;1"
            data "Description" "h1e2c767dg93ccg472bg8d5dgd990bf0ac8bf;7"
            data "DescriptionParams" "DealDamage(1d6,Necrotic)"
            data "ExtraDescription" "he5dbb5b3gcdccg43ceg967agdea5e47fafe0;3"
            data "TooltipDamageList" "DealDamage(1d6,Necrotic,,,,ad727a13-c6f0-4b5b-aefd-aac79c6ed46e)"
            data "TooltipUpcastDescription" "6ff1780a-855a-414c-a8bf-811251537206"
            data "CastSound" "Spell_Cast_Debuff_Hex_L1to3"
            data "TargetSound" "Spell_Impact_Debuff_Hex_L1to3"
            data "VocalComponentSound" "Vocal_Component_Curse"
            data "CastTextEvent" "Cast"
            data "CycleConditions" "Enemy() and not Dead()"
            data "UseCosts" "BonusActionPoint:1; SpellSlotsGroup:1:1:1"
            data "SpellAnimation" "9313094a-bae2-454f-9701-f920d0e8e98d,,;,,;ab7b6aac-b3c9-4918-8f17-f777a94dcb5e,,;57211a11-ed0b-46d7-9369-81df25a85df6,,;808fdfab-2e6c-472e-b3c4-19ce4a719d9d,,;,,;ea745d30-eb87-447f-b190-c81298e27d9c,,;,,;,,"
            data "VerbalIntent" "Debuff"
            data "SpellStyleGroup" "Class"
            data "SpellFlags" "HasVerbalComponent;HasSomaticComponent;IsConcentration;IsSpell;IsLinkedSpellContainer;IsHarmful"
            data "MemoryCost" "1"
            data "PrepareEffect" "db4fd7eb-049e-43d0-95ce-d8f5bc808c0c"
            data "CastEffect" "d9cc11d0-ef2a-4c79-aaf4-7916a51f56a6"
            data "TargetEffect" "ef1cdb0d-28ae-4989-b8b8-09438f749a00"\
        """),

        'no_spell_container_id': textwrap.dedent("""\
            new entry "Target_Summon_MudMephit"
            type "SpellData"
            data "SpellType" "Target"
            using "Target_RangersCompanion"
            data "SpellSchool" "None"
            data "SpellContainerID" ""
            data "ContainerSpells" ""
            data "Cooldown" "OncePerTurn"
            data "AIFlags" ""
            data "SpellProperties" "GROUND:Summon(02b5e1ea-389d-4008-a247-66538709388b,Permanent, Projectile_AiHelper_Summon_Weak,);AI_IGNORE:GROUND:CreateSurface(1, -1, None)"
            data "Requirements" ""
            data "TargetConditions" "not Character() and not Item() and Surface('SurfaceMud')"
            data "Icon" "GenericIcon_Intent_Summon"
            data "DisplayName" "hef45f8b2gd1e1g4153g9628gc3fb6a33f492;1"
            data "Description" "hece897c2g4233g4248g883egaed18415d42f;1"
            data "CastSound" "CrSpell_Cast_MudMephitMuddyFriends"
            data "TargetSound" "CrSpell_Impact_MudMephitMuddyFriends"
            data "CastTextEvent" "VFX_Somatic_01"
            data "UseCosts" "ActionPoint:1;SpellSlotsGroup:1:1:1"
            data "SpellAnimation" "20bc8606-6406-4f04-a0f7-ec458125b663,,;8f5c3b68-2383-4470-bb15-ca3e9b6c5819,,;36fcebc4-6813-48f0-81f0-c473b79782b7,,;6e5625e7-7912-450f-9375-d42491d31335,,;7a4db7bc-d962-4e4c-9ac8-c2f03b96a370,,;,,;f2849708-05fa-405a-ba15-3bacbe1a3d56,,;,,;,,"
            data "SpellFlags" "IgnoreSilence;IsEnemySpell;HasHighGroundRangeExtension"
            data "RechargeValues" "4-6"
            data "SpellAnimationIntentType" "Aggressive"
            data "MemoryCost" ""
            data "PrepareEffect" "7642df71-e717-4a3a-a5ee-482b29ce3e65"
            data "CastEffect" "20235cdf-4ca6-4412-bb2d-5ea20cc33705"
            data "TargetEffect" "995013d2-ac87-400e-adfa-c7aa3f2b949d"
            data "Sheathing" "DontChange"\
        """),

        'scorchingray': textwrap.dedent("""\
            new entry "Projectile_ScorchingRay"
            type "SpellData"
            data "SpellType" "Projectile"
            data "Level" "2"
            data "SpellSchool" "Evocation"
            data "SpellProperties" "GROUND:SurfaceChange(Ignite);GROUND:SurfaceChange(Melt)"
            data "TargetFloor" "-1"
            data "TargetRadius" "18"
            data "AmountOfTargets" "3"
            data "SpellRoll" "Attack(AttackType.RangedSpellAttack)"
            data "SpellSuccess" "DealDamage(2d6,Fire,Magical)"
            data "TargetConditions" "not Self() and not Dead()"
            data "ProjectileCount" "1"
            data "CastTargetHitDelay" "100"
            data "Trajectories" "76dc68a0-5bc5-4ffc-be02-547f690af36b"
            data "Icon" "Spell_Evocation_ScorchingRay"
            data "DisplayName" "h0b8ccf68g4ea7g4d92g9c77g6ab716600ab0;1"
            data "Description" "h8683be5fg3434g4e62g8027g3275339e7735;4"
            data "DescriptionParams" "DealDamage(2d6,Fire);3"
            data "TooltipDamageList" "DealDamage(6d6,Fire)"
            data "TooltipAttackSave" "RangedSpellAttack"
            data "TooltipUpcastDescription" "f59d4740-0a34-49ff-90e1-cbe0a668f370"
            data "PrepareSound" "Spell_Prepare_Damage_Fire_Gen_L1to3"
            data "PrepareLoopSound" "Spell_Prepare_Damage_Fire_Gen_L1to3_Loop"
            data "CastSound" "Spell_Cast_Damage_Fire_ScorchingRay_L0"
            data "CastTextEvent" "Cast"
            data "CycleConditions" "Enemy() and not Dead()"
            data "UseCosts" "ActionPoint:1;SpellSlotsGroup:1:1:2"
            data "SpellAnimation" "3ff87abf-1ea1-4c32-aadf-c822d74c7dc0,,;,,;cd5e5d4a-38e1-4d4d-b346-3fbc1e4c3c90,,;141f48d9-9615-496a-8737-9240f0dba60d,,;d8925ce4-d6d9-400c-92f5-ad772ef7f178,,;,,;eadedcce-d01b-4fbb-a1ae-d218f13aa5d6,,;,,;,,"
            data "VerbalIntent" "Damage"
            data "SpellFlags" "IsSpell;HasHighGroundRangeExtension;HasSomaticComponent;HasVerbalComponent;RangeIgnoreVerticalThreshold;IsHarmful"
            data "HitAnimationType" "MagicalDamage_External"
            data "RechargeValues" "5-6"
            data "MemoryCost" "1"
            data "PrepareEffect" "c88e9cfa-df92-477a-ae75-cbfb932350b4"
            data "CastEffect" "4481fb37-77c2-4b70-8675-01638932c01b"
            data "DamageType" "Fire"\
        """),

        'scorchingray_3': textwrap.dedent("""\
            new entry "Projectile_ScorchingRay_3"
            type "SpellData"
            data "SpellType" "Projectile"
            using "Projectile_ScorchingRay"
            data "AmountOfTargets" "4"
            data "DescriptionParams" "DealDamage(2d6,Fire);4"
            data "TooltipDamageList" "DealDamage(8d6,Fire)"
            data "UseCosts" "ActionPoint:1;SpellSlotsGroup:1:1:3"
            data "RootSpellID" "Projectile_ScorchingRay"
            data "PowerLevel" "3"\
        """),

        'spell_container_id': textwrap.dedent("""\
            new entry "Target_EnsnaringStrike"
            type "SpellData"
            data "SpellType" "Target"
            using "Target_MainHandAttack"
            data "Level" "1"
            data "SpellSchool" "Conjuration"
            data "SpellContainerID" "Projectile_EnsnaringStrike_Container"
            data "TargetRadius" "MeleeMainWeaponRange"
            data "SpellRoll" "Attack(AttackType.MeleeWeaponAttack)"
            data "SpellSuccess" "IF(not SavingThrow(Ability.Strength, SourceSpellDC(),AdvantageOnRestrained(),DisadvantageOnRestrained())):ApplyStatus(ENSNARING_STRIKE,100,10);DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType); ExecuteWeaponFunctors(MainHand)"
            data "TargetConditions" "Character() and not Self()"
            data "Icon" "Spell_Conjuration_EnsnaringStrikeMelee"
            data "DisplayName" "heac6a8e1g6248g4146g8901g3651a219b8dc;1"
            data "Description" "h61f1d020g7de5g494bg96a6g746ccfa68fd5;2"
            data "TooltipDamageList" "DealDamage(MainMeleeWeapon, MainMeleeWeaponDamageType)"
            data "TooltipAttackSave" "Strength"
            data "TooltipStatusApply" "ApplyStatus(ENSNARING_STRIKE,100,10)"
            data "TooltipUpcastDescription" "43370bc5-39c2-4d65-bc0e-4e9acfab0c80"
            data "TooltipUpcastDescriptionParams" "DealDamage(1d6,Piercing)"
            data "CastSound" "Spell_Cast_Damage_Physical_EnsnaringStrike_L1to3"
            data "TargetSound" "Spell_Impact_Damage_Physical_EnsnaringStrike_L1to3"
            data "PreviewCursor" "Melee"
            data "CastTextEvent" "Cast"
            data "HitCosts" "BonusActionPoint:1;SpellSlotsGroup:1:1:1"
            data "SpellAnimation" "2ba949b7-0329-4190-992c-11b0d29183c5,,;9583ecee-cf6c-4735-86db-7ebf1df15eae,,;de006e3f-70fb-4eb7-a98d-d845d15b20e8,,;50696db7-d931-4734-915d-32d038ba99a5,,;a0503ad0-c1b1-449c-b431-4ac6c39c58d7,,;c36ed247-2272-492b-99c2-2ca10b014670,,;0b07883a-08b8-43b6-ac18-84dc9e84ff50,,;,,;,,"
            data "DualWieldingSpellAnimation" "c25d80c5-aaf3-4aba-bc1f-bb1c8534725e,,;45bcbbd4-f9ca-4b19-88c2-822c5e2b0d8b,,;466e7470-712f-4a67-8ef1-5908a20b0449,,;c1713221-163b-4bae-95de-e6681d665c76,,;dc83b386-41f5-43df-9649-788107052830,,;b63dee1e-08e1-4f7a-88ee-1e6baa38e0dd,,;0b07883a-08b8-43b6-ac18-84dc9e84ff50,,;,,;,,"
            data "VerbalIntent" "Control"
            data "SpellStyleGroup" "Class"
            data "WeaponTypes" "Melee"
            data "SpellFlags" "HasVerbalComponent;IsSpell;IsMelee;IsConcentration;IsHarmful"
            data "MemoryCost" "1"
            data "PrepareEffect" "1ffb0671-f398-4cb5-a3c0-3ed4b15a5f10"
            data "CastEffect" "48611453-6d8e-470a-8f88-c30ab9875d89"
            data "TargetEffect" "00b0965a-b9cf-4f39-8b5b-49df3fc43f86"
            data "Sheathing" "Melee"\
        """),
    }
    for spell_name, block in blocks.items():
        test_blocks[spell_name] = block


""" Invoke tests when called directly """

if __name__ == "__main__":
    pytest.main()
