#!/usr/bin/env python

""" Script to modify contents of character file """

import copy
import os
import re
import sys

mod_name = "MetamagicExtended"

spells_ignored = [
    '.*_DEPRECATED_.*',
    'Projectile_[A-Z]{3}_.*',
    'Projectile_EnsnaringStrike.*',
    'Projectile_Smite.*',
    'Projectile_ProduceFlame.*',
    'Projectile_WitchBolt.*',
    'Target_[A-Z]{3}_.*',
    'Target_CallLightning.*',
    'Target_ConjureElemental.*',
    'Target_ElementalWeapon.*',
    'Target_EnsnaringStrike.*',
    'Target_Eyebite_.*',
    'Target_HeatMetal.*',
    'Target_Hex.*',
    'Target_GlyphOfWarding.*',
    'Target_ProtectionFromEnergy.*',
    'Target_Smite.*',
    'Target_StaggeringSmite.*',
    'Shout_[A-Z]{3}_.*',
    'Shout_AlterSelf.*',
    'Shout_FireShield_Chill',
    'Shout_SpiritGuardians_.*',
    'Wall_[A-Z]{3}_.*',
    'Zone_[A-Z]{3}_.*',
    'Zone_Sunbeam.*',
    '.*_(LOW|MAG|SHA|WYR)_.*',
    '.*_Activate',
    '.*_Djinni',
    '.*_Dryad',
    '.*_Githyanki',
    '.*_Gnoll',
    '.*_Gortash',
    '.*_HellishRebuke.*',
    '.*_Hurl',
    '.*_Mindflayer',
    '.*_Recast',
    '.*_Red[Cc]ap',
    '.*_Throw',
    '.*_WoodWoad',
    '.*_[0-9]',
]


class Spell(object):
    def __init__(self, name, raw, debug=False):
        self.name = name
        self.data = {}
        self.using = ""
        self._raw = raw
        self._supported_elements = [
            "Acid",
            "Cold",
            "Fire",
            "Lightning",
            "Thunder"
        ]
        self._non_transmutable_spells = [
            'Projectile_ChromaticOrb.*',
            'Projectile_GlyphOfWarding.*',
        ]

        for line in self._raw:
            m = re.match(r'data "(?P<key>[^"]+)" "(?P<value>[^"]+)"', line)
            if m:
                k = m.group('key')
                v = m.group('value')
                self.data[k] = v

            m = re.match(r'using "(?P<parent>[^=]+)"', line)
            if m:
                self.using = m.group('parent')

    def __eq__(self, other):
        return self.name == other.name

    def __gt__(self, other):
        return self.name < other.name

    def __lt__(self, other):
        return self.name < other.name

    def __ne__(self, other):
        return self.name != other.name

    def __repr__(self):
        spell_type = self.data['SpellType']
        lines = [
            f'new entry "{self.name}"',
            f'type "SpellData"',
            f'data "SpellType" "{spell_type}"',
        ]

        if self.using:
            lines.append(f'using "{self.using}"')

        for k, v in self.data.items():
            if k == 'SpellType':
                continue
            if k == 'ContainerSpells':
                v = ';'.join(sorted(v.split(';')))
            lines.append(f'data "{k}" "{v}"')

        return "\n".join(lines)

    def add_item(self, param, value):
        """ Add a unique value from a parameter """
        values = set()
        found = self.data.get(param, None)
        if found:
            values = set(found.split(';'))
        values.add(value)
        self.data[param] = ';'.join(values)

    def append_string(self, param, s):
        """ Appends string to parameter """
        value = s
        found = self.data.get(param, None)
        if found:
            value += f"and {found}"
        self.data[param] = value

    def damage_type(self):
        return self.data['DamageType']

    def base(self):
        """ Adds a base variant of the spell to container """
        base_spell = self.get_child('Base')
        base_spell.using = self.name

        """ Containerize """
        base_spell.set_item('ContainerSpells', "")
        base_spell.set_item('SpellContainerID', self.name)

        return base_spell

    def detach(self):
        detached_spell = self.get_child('Detached')
        detached_spell.using = self.name

        """ Detach """
        detached_spell.set_item('SpellFlags', self.data['SpellFlags'])
        detached_spell.remove_item('SpellFlags', 'IsConcentration')

        """ Containerize """
        detached_spell.set_item('ContainerSpells', "")
        detached_spell.set_item('SpellContainerID', self.name)

        """ Make conditional """
        level = self.data.get('Level', 1)
        detached_spell.set_item('UseCosts', self.data['UseCosts'])
        detached_spell.add_item(
            'UseCosts', f'Detachment_Charge:1'
        )

        return detached_spell

    def is_concentration(self):
        if not self.is_spell():
            return False

        flags = self.data.get('SpellFlags', None)
        if not flags:
            return False

        if "IsConcentration" in flags.split(';'):
            return True

        return False

    def is_spell(self):
        flags = self.data.get('SpellFlags', None)
        if not flags:
            return False

        return "IsSpell" in flags.split(';')

    def is_transmutable(self):
        if not self.is_spell():
            return False

        """ Skip non-transmutable spells """
        exceptions_re = "({})".format('|'.join(self._non_transmutable_spells))
        if re.match(f'({exceptions_re})', self.name):
            return False

        if self.data.get('DamageType', None) in self._supported_elements:
            return True

        return False

    def get_child(self, postfix):
        spell_name = f"{self.name}_{postfix}"
        spell_type = self.data['SpellType']

        raw = '\n'.join([
            f'new entry "{spell_name}"',
            f'type "SpellData"',
            f'data "SpellType" "{spell_type}"',
            f'using "{self.name}"',
        ])

        child_spell = Spell(name=spell_name, raw=raw)
        # TODO: debug, this should not be necessary
        child_spell.set_item('SpellType', spell_type)
        return child_spell

    def transmute(self):
        transmuted_spells = []

        for element in self._supported_elements:
            transmuted_spell = self.get_child(element)
            transmuted_spell.using = self.name
            transmuted_spell.set_item('DamageType', element)

            """ Replace element in relevant data fields """
            damage_re = re.compile(
                r'DealDamage\(([^,]+),(Acid|Cold|Fire|Lightning|Thunder)(.*)\)'
            )
            replace_re = r'DealDamage(\1,{}\3)'.format(element)

            for field in ['DescriptionParams', 'TooltipDamageList', 'SpellFail', 'SpellProperties', 'SpellSuccess']:
                found = self.data.get(field, None)
                if found:
                    found = re.sub(damage_re, replace_re, found)
                transmuted_spell.data[field] = found

            """ Containerize """
            transmuted_spell.set_item('ContainerSpells', "")
            transmuted_spell.set_item('SpellContainerID', self.name)

            """ Transmuted variant cost and condition """
            if self.data['DamageType'] != element:
                transmuted_spell.set_item('UseCosts', self.data['UseCosts'])
                transmuted_spell.add_item(
                    'UseCosts', 'Transmutation_Charge:1'
                )

            transmuted_spells.append(transmuted_spell)

        return transmuted_spells

    def remove_item(self, param, value):
        """ Remove a unique value from a parameter """
        found = self.data.get(param, None)
        if found:
            values = set(found.split(';'))
            values.remove(value)
            if len(values) == 0:
                return
            self.data[param] = ';'.join(values)

    def register_container_spell(self, spell):
        self.add_item('ContainerSpells', spell.name)
        self.add_item('SpellFlags', 'IsLinkedSpellContainer')

    def set_item(self, param, value):
        """ Remove a unique value from a parameter """
        self.data[param] = value


def usage():
    print("prep.py source_file")
    sys.exit(1)


def get_options(args):
    """ Returns options from command line """
    nargs = len(sys.argv)
    if nargs < 2:
        usage()

    source = sys.argv[1]
    if not os.path.exists(source):
        print(f"No such file: {source}")
        sys.exit(2)

    return source


def parse(source):
    spells = {}
    with open(source, "r") as f:
        for block in f.read().split('\n\n'):
            if len(block) == 0:
                continue

            lines = block.split('\n')
            if len(lines) < 3:
                continue

            """ Obtain spell name """
            m = re.match(r'new entry "(?P<name>[^"]+)"', lines[0])
            if not m:
                print(f"parsing issue in block")
                continue
            name = m.group('name')

            """ Skip ignored spells """
            spells_ignored_re = "({})".format('|'.join(spells_ignored))
            if re.match(spells_ignored_re, name):
                print(f"[-] skipping ignored spell {name}")
                continue

            """ Skip non-spells (other actions) """
            is_spell = False
            for line in lines:
                m = re.match(r'data "SpellFlags" "(?P<flags>[^"]+)"', line)
                if m:
                    is_spell = 'IsSpell' in set(m.group('flags').split(';'))
                    break

            if not is_spell:
                continue

            spells[name] = Spell(name, lines)

    return spells


def modify_spells(source):
    """ Adds transmuted spell variants """
    data = parse(source)
    for name, spell in data.items():
        meta_spells = []
        target = f"modded/Spell_{name}.txt"

        if spell.is_concentration():
            print(f"[C] {name}")
            """ Unmodified variant """
            base_spell = spell.base()
            spell.register_container_spell(base_spell)
            meta_spells.append(base_spell)

            """ Detached variant """
            detached_spell = spell.detach()
            spell.register_container_spell(detached_spell)
            meta_spells.append(detached_spell)

        if spell.is_transmutable():
            print(f"[T] {name}")
            """ Transmuted variant, one for each element """
            for tspell in spell.transmute():
                spell.register_container_spell(tspell)
                meta_spells.append(tspell)

        """ Write to file if feasible to meta """
        if len(meta_spells) > 0:
            with open(target, "w") as f:
                f.write("{}\n\n".format(spell))
                for meta_spell in meta_spells:
                    f.write("{}\n\n".format(meta_spell))


if __name__ == "__main__":
    source = get_options(sys.argv)
    modify_spells(source)
