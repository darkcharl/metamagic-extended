#!/usr/bin/env python

""" Script to create meta spell variants """

import copy
import os
import re
import sys

mod_name = "MetamagicExtended"

detached_index = set()
transmuted_index = set()

spells_ignored = [
    '.*_DEPRECATED_.*',
    'Projectile_[A-Z]{3}_.*',
    'Projectile_EnsnaringStrike.*',
    'Projectile_Smite.*',
    'Projectile_ProduceFlame.*',
    'Projectile_WitchBolt.*',
    'Target_[A-Z]{3}_.*',
    'Target_BestowCurse.*',
    'Target_CallLightning.*',
    'Target_ConjureElemental.*',
    'Target_ElementalWeapon.*',
    'Target_EnhanceAbility.*',
    'Target_Enlarge.*',
    'Target_EnsnaringStrike.*',
    'Target_Eyebite.*',
    'Target_GlyphOfWarding.*',
    'Target_HeatMetal.*',
    'Target_Hex.*',
    'Target_ProtectionFromEnergy.*',
    'Target_Reduce.*',
    'Target_Smite.*',
    'Target_StaggeringSmite.*',
    'Throw_*',
    'Shout_[A-Z]{3}_.*',
    'Shout_AlterSelf.*',
    'Shout_FireShield_Chill',
    'Shout_SpiritGuardians.*',
    'Wall_[A-Z]{3}_.*',
    'Zone_[A-Z]{3}_.*',
    'Zone_Sunbeam.*',
    '.*_(LOW|MAG|SHA|WYR)_.*',
    '.*_Activate',
    '.*_AI',
    '.*_Djinni',
    '.*_Dragon',
    '.*_Dryad',
    '.*_Githyanki',
    '.*_Gnoll',
    '.*_Gortash',
    '.*_HellishRebuke.*',
    '.*_Hurl',
    '.*_Mindflayer',
    '.*_Monk',
    '.*_Recast',
    '.*_Red[Cc]ap',
    '.*_Skeletal',
    '.*_Throw',
    '.*_Trap',
    '.*_WoodWoad',
]


class Spell(object):
    def __init__(self, name, raw, leveled=False):
        self.name = name
        self._base_name = ""
        self.data = {}
        self.using = ""
        self._raw = raw
        self._instrumented = False
        self._leveled = leveled
        self._level = -1
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

        m = re.match(r'(?P<base_name>.*)_(?P<level>[0-9])', self.name)
        if m:
            self._leveled = True
            self._base_name = m.group('base_name')
            self._level = m.group('level')

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
        self.data[param] = ';'.join(sorted(values))

    def append_string(self, param, s):
        """ Appends string to parameter """
        value = s
        found = self.data.get(param, None)
        if found:
            value += f"and {found}"
        self.data[param] = value

    def damage_type(self):
        return self.data['DamageType']

    def base(self, postfix='Base'):
        """ Adds a base variant of the spell to container """
        base_spell = self.get_child(postfix)

        """ Containerize """
        root_spell_id = self.data.get('RootSpellID', None)
        if self.is_leveled():
            root_spell_id = f"{self._base_name}_{postfix}"
            base_spell.set_item('RootSpellID', root_spell_id)
            base_spell.set_item('SpellContainerID', self.name)
            base_spell.set_item('ContainerSpells', "")
            base_spell.using = self.name
        else:
            base_spell.set_item('ContainerSpells', "")
            base_spell.set_item('SpellContainerID', self.name)
            base_spell.using = self.name

        return base_spell

    def detach(self, postfix='Detached'):
        self._instrumented = True
        detached_spell = self.get_child(postfix)
        sorcery_point_cost = 1

        """ Explicitly unset to avoid inheritance """
        detached_spell.set_item('ContainerSpells', "")
        detached_spell.data.pop('SpellFlags', None)

        """ Containerize """
        if self.is_leveled():
            """ Derivative, leveled spell """
            sorcery_point_cost = self._level
            root_spell_id = f"{self._base_name}_{postfix}"
            detached_spell.set_item('RootSpellID', root_spell_id)
            detached_spell.set_item('SpellContainerID', self.name)
            detached_spell.using = self.name
            detached_spell.remove_item('SpellFlags', 'IsLinkedSpellContainer')
            detached_spell.set_item('PowerLevel', self._level)
        else:
            """ We are acting on the main spell """
            detached_spell.set_item('SpellFlags', self.data['SpellFlags'])
            detached_spell.remove_item('SpellFlags', 'IsConcentration')
            detached_spell.set_item('SpellContainerID', self.name)
            detached_spell.using = self.name

        """ Set cost, make conditional """

        detached_spell.set_item('UseCosts', self.data.get('UseCosts', ''))
        detached_spell.add_item(
            'UseCosts', f'SorceryPoint:{sorcery_point_cost};DetachmentCharge:1'
        )

        return detached_spell

    def is_detachable(self):
        if self._base_name and self._base_name in detached_index:
            return True

        if not self.is_spell():
            return False

        flags = self.data.get('SpellFlags', None)
        if not flags:
            return False

        if "IsConcentration" in flags.split(';'):
            return True

        return False

    def is_instrumented(self):
        return self._instrumented

    def is_leveled(self):
        return self._leveled

    def is_spell(self):
        if self.is_leveled():
            return True

        flags = self.data.get('SpellFlags', None)
        if not flags:
            return False

        return "IsSpell" in flags.split(';')

    def is_transmutable(self):
        if self._base_name and self._base_name in transmuted_index:
            return True

        if not self.is_spell():
            return False

        """ Skip non-transmutable spells """
        exceptions_re = "({})".format('|'.join(self._non_transmutable_spells))
        if re.match(f'({exceptions_re})', self.name):
            return False

        # for property in ['SpellSuccess', 'SpellFail']:
        #    v = self.data.get(property, None)
        #    m = re.find()

        if self.data.get('DamageType', None) in self._supported_elements:
            return True

        return False

    def get_child(self, postfix):
        spell_name = f"{self.name}_{postfix}"
        if self.is_leveled():
            spell_name = f"{self._base_name}_{postfix}_{self._level}"

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
        self._instrumented = True
        sorcery_point_cost = 1

        for element in self._supported_elements:
            transmuted_spell = self.get_child(element)

            # orig_elem = self.data.get('DamageType', None)
            # if orig_elem and orig_elem == element:
            #    """ Don't transmute default element """
            #    continue

            transmuted_spell.set_item('DamageType', element)

            """ Replace element in relevant data fields """
            damage_re = re.compile(
                r'DealDamage\(([^,]+),(Acid|Cold|Fire|Lightning|Thunder)(.*)\)'
            )
            replace_re = r'DealDamage(\1,{}\3)'.format(element)

            for field in ['DescriptionParams', 'TooltipDamageList', 'SpellFail', 'SpellProperties', 'SpellSuccess']:
                found = self.data.get(field, '')
                if found:
                    found = re.sub(damage_re, replace_re, found)
                    transmuted_spell.data[field] = found

            """ Explicitly unset to avoid inheritance """
            transmuted_spell.set_item('ContainerSpells', "")
            transmuted_spell.data.pop('SpellFlags', "")

            """ Containerize """
            if self.is_leveled():
                root_spell_id = f"{self._base_name}_{element}"
                transmuted_spell.set_item('RootSpellID', root_spell_id)
                transmuted_spell.set_item('SpellContainerID', self.name)
                transmuted_spell.remove_item(
                    'SpellFlags', 'IsLinkedSpellContainer')
                transmuted_spell.using = self.name
                transmuted_spell.set_item('PowerLevel', self._level)
            else:
                transmuted_spell.set_item('SpellContainerID', self.name)
                transmuted_spell.using = self.name

            """ Transmuted variant cost and condition """
            transmuted_spell.set_item('UseCosts', self.data['UseCosts'])
            transmuted_spell.add_item(
                'UseCosts', f'SorceryPoint:{sorcery_point_cost};TransmutationCharge:1'
            )

            transmuted_spells.append(transmuted_spell)

        return transmuted_spells

    def remove_item(self, param, value):
        """ Remove a unique value from a parameter """
        found = self.data.get(param, '')
        if found:
            values = set(found.split(';'))
            values.remove(value)
            if len(values) == 0:
                return
            self.data[param] = ';'.join(sorted(values))

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
        """ Parse source """
        for block in f.read().split('\n\n'):
            if len(block) == 0:
                continue

            lines = block.split('\n')
            if len(lines) < 3:
                continue

            """ Obtain spell name """
            m = re.match(
                r'new entry "(?P<name>[^"]+)"', lines[0])
            if not m:
                print(f"parsing issue in block")
                continue
            name = m.group('name')
            is_leveled = name.split('_')[-1].isnumeric()

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

            if is_spell or is_leveled:
                spells[name] = Spell(name, lines, is_leveled)
                continue

            print(f"[-] skipping non-spell {name}")

    return spells


def modify_spells(source):
    """ Adds transmuted spell variants """

    """ Load and parse spell file """
    data = parse(source)

    for name, spell in data.items():
        meta_spells = []
        target = f"modded/Spell_{name}.txt"

        if spell.is_detachable():
            print(f"[C] {name}")

            """ Register non-leveled spell in index """
            if not spell.is_leveled():
                detached_index.add(name)

            """ Detached variant """
            detached_spell = spell.detach()
            spell.register_container_spell(detached_spell)

            meta_spells.append(detached_spell)

        if spell.is_transmutable():
            print(f"[T] {name}")

            """ Register non-leveled spell in index """
            if not spell.is_leveled():
                transmuted_index.add(name)

            """ Transmuted variant, one for each element """
            for transmuted_spell in spell.transmute():
                spell.register_container_spell(transmuted_spell)
                meta_spells.append(transmuted_spell)

        """ Create unmodified variant """
        if spell.is_instrumented():
            base_spell = spell.base()
            spell.register_container_spell(base_spell)
            meta_spells.append(base_spell)

        """ Write modified spells to file """
        if len(meta_spells) > 0:
            with open(target, "w") as f:
                if spell.is_leveled():
                    spell.data.pop('SpellFlags', '')
                f.write("{}\n\n".format(spell))
                for meta_spell in meta_spells:
                    f.write("{}\n\n".format(meta_spell))


def read_index(filename):
    with open(filename, "r") as idx:
        spell_index = set(idx.read().split('\n'))
    return spell_index


def write_index(filename, index):
    with open(filename, "w") as idx:
        idx.write('\n'.join(sorted(index)))


if __name__ == "__main__":
    source = get_options(sys.argv)
    """ Read spell index """
    detached_index = read_index("detached.idx")
    transmuted_index = read_index("transmuted.idx")

    modify_spells(source)

    write_index("detached.idx", detached_index)
    write_index("transmuted.idx", transmuted_index)
