#!/usr/bin/env python

import argparse
import copy
import glob
import re


class SpellFilterOptions:
    def __init__(self, **kwargs):
        self.base = None
        self.concentration = None
        self.container = None
        self.debug = None
        self.descendants = None
        self.dest = 'modded'
        self.elemental = None
        self.enabled = None
        self.harmful = None
        self.leveled = None
        self.members = None
        self.path = None
        self.spell = None
        self.spellname = None
        self.verbose = None
        for k, v in kwargs.items():
            setattr(self, k, v)


class SpellParseException(Exception):
    def __init__(self, message):
        """ Raised when the spell cannot be parsed """
        self.message = message


class SpellLinkException(Exception):
    def __init__(self, message):
        """ Raised when the spell cannot be linked """
        self.message = message


class Spell:
    def __init__(self, **kwargs):
        """ Spell object """
        self.name = kwargs.get('name', None)
        self.type = kwargs.get('type', None)
        self.using = kwargs.get('using', None)
        self.data = kwargs.get('data', {})

        """ If using text data to initialize """
        self.block = kwargs.get('block', None)

        """ Internal object refs for inheritance tracking """
        self.children = set()
        self.parent = None

        """ Internal object refs for containerization tracking """
        self.container = None
        self.members = set()
        self.upleveled = set()

        """ Internal object refs for tracking original spells """
        self.originals = {}

        """ If not using a text block to initialize, return """
        if self.block != None:
            self.parse_block()

    def parse_block(self):
        """ Text based Spell object initiatization """

        """ Simple format checks """
        lines = self.block.split('\n')
        if len(lines) < 3:
            raise SpellParseException('too few lines')
        elif lines[0][:9] != "new entry":
            raise SpellParseException('missing spell name header')
        elif lines[1][:16] != 'type "SpellData"':
            raise SpellParseException('missing type field')

        """ Critical properties check """
        self.name = re.sub('new entry "([^"]+)"', r'\1', lines[0])
        self.type = re.sub('data "SpellType" "([^"]+)"', r'\1', lines[2])
        if not self.name or not self.type:
            raise SpellParseException('no name or type')

        """ Processing of spell data """
        for line in lines[3:]:
            is_data = re.match(
                'data "(?P<attribute>[^"]+)" "(?P<value>[^"]*)"', line)
            if not is_data:
                has_using = re.match('using "(?P<using>[^"]+)"', line)
                if has_using:
                    self.using = has_using.group('using')
                    continue
                raise SpellParseException(f'invalid line {line}')
            self.data[is_data.group('attribute')] = is_data.group('value')

    @property
    def container_spells(self):
        spells_flat = self.data.get('ContainerSpells', None)
        if not spells_flat:
            return set()
        return set(spells_flat.split(';'))

    @property
    def damage_type(self):
        return self.data.get('DamageType', None)

    @property
    def flags(self):
        flags_flat = self.data.get('SpellFlags', None)
        if not flags_flat:
            return set()
        return set(flags_flat.split(';'))

    @property
    def joined_flags(self):
        return self.data.get('SpellFlags', None)

    @property
    def joined_children(self):
        return ';'.join([str(s) for s in self.children])

    @property
    def joined_members(self):
        return ';'.join([str(s) for s in self.members])

    @property
    def joined_upleveled(self):
        return ';'.join([str(s) for s in self.upleveled])

    @property
    def level(self):
        return int(self.data.get('PowerLevel', 0)) or int(self.data.get('Level', 0))

    @property
    def requirement_condition(self):
        cond = self.data.get('RequirementCondition', None)
        if not cond:
            return set()
        return set(cond.split(' and '))

    @property
    def root_spell_id(self):
        return self.data.get('RootSpellID', None)

    @property
    def spell_container_id(self):
        return self.data.get('SpellContainerID', None)

    @property
    def transmutable_elements(self):
        if not self.is_elemental():
            return []
        elements = set(('Acid', 'Cold', 'Fire', 'Lightning', 'Thunder'))
        elements.remove(self.damage_type)
        return elements

    @property
    def use_costs(self):
        use_costs = self.data.get('UseCosts', None)
        if not use_costs:
            return set()
        return set(use_costs.split(';'))

    def add_cost(self, value):
        """ Adds a cost to the use costs field """
        uc = self.use_costs
        uc.add(value)
        self.data['UseCosts'] = ';'.join(sorted(uc))

    def add_member(self, spell):
        """ Adds spell to this spell container """
        cs = self.container_spells
        self.members.add(spell)
        cs.add(spell.name)
        self.data['ContainerSpells'] = ';'.join(sorted(cs))

    def add_members(self, spells):
        """ Adds spells as container spells to this spell container """
        for spell in spells:
            self.add_member(spell)

    def add_requirement_condition(self, value):
        """ Adds requirement condition to spell """
        cond = self.requirement_condition
        cond.add(value)
        self.data['RequirementConditions'] = ' and '.join(cond)

    def containerize(self):
        """ Turns this spell into a linked spell container """
        self.set_flag('IsLinkedSpellContainer')
        self.data['ContainerSpells'] = self.data.get('ContainerSpells', '')

    def copy_attribute(self, other_spell, attributes):
        """ Copies select list of attributes from another spell"""
        for attr in attributes:
            found = getattr(other_spell, attr)
            if found:
                setattr(self, attr, found)

    def copy_data(self, other_spell, properties):
        """ Copies select list of data (properties) from another spell"""
        for p in properties:
            found = other_spell.data.get(p, None)
            if found:
                self.data[p] = found

    def create_meta(self, postfix, deprioritized=False):
        if deprioritized:
            new_name = f"_{self.postfix_name(postfix)}"
            root_name = f"_{self.postfix_root_spell_id(postfix)}"
        else:
            new_name = f"{self.postfix_name(postfix)}"
            root_name = f"{self.postfix_root_spell_id(postfix)}"
        s = self.duplicate(new_name)
        s.set_container(self)
        s.set_root_spell_id(root_name)
        return s

    def create_originals(self, postfix='Original'):
        """ 
        Creates a duplicate of the spell and its upleveled variants

        Links the created spells in a map, keyed after the original spell name

        For example:
        {
            Target_Bless => Target_Bless_Original,
            Target_Bless_2 => Target_Bless_Original_2,
        }

        """
        self.originals = {
            self.name: self.duplicate(name=self.postfix_name(postfix))
        }
        for spell in self.upleveled:
            spell.using = f"{spell.postfix_using(postfix)}"
            # if spell.is_leveled():
            #    spell.data['RootSpellID'] = f"{spell.postfix_name(postfix)}"
            self.originals[spell.name] = spell.duplicate(
                name=f"{spell.postfix_name(postfix)}")
        return self.originals.values()

    def decontainerize(self):
        """ Ensures the spell is not a container """
        self.unset_flag('IsLinkedSpellContainer')
        self.data['ContainerSpells'] = ''

    def duplicate(self, name=None):
        """ Copies and returns the copy of this spell """
        spell = Spell(
            name=self.name,
            type=self.type,
            data=copy.copy(self.data),
            using=self.using,
        )
        if name:
            spell.name = name
        return spell

    def get_upleveled_chain(self):
        """ Returns this spell and its upleveled spell variants as a list """
        spells = [self]
        spells.extend(self.upleveled)
        return spells

    def has_container_spells(self):
        return self.data.get('ContainerSpells', None)

    def has_flag(self, flag):
        return flag in self.flags

    def has_no_container_spells(self):
        return not self.has_spell_container()

    def has_no_using(self):
        return not self.has_using()

    def has_using(self):
        return self.using

    def has_root_spell(self):
        return self.data.get('RootSpellID', None)

    def has_spell_container(self):
        return self.data.get('SpellContainerID', None)

    def inherit(self, spell, attribute='SpellFlags'):
        value = self.data.get(attribute, None)
        if not value:
            self.data[attribute] = spell.data.get(attribute, "")

    def is_concentration(self):
        return self.has_flag('IsConcentration')

    def is_connected(self):
        return self.has_root_spell() or self.has_spell_container()

    def is_container(self):
        return self.has_flag('IsLinkedSpellContainer')

    def is_elemental(self):
        return self.damage_type in ['Acid', 'Cold', 'Fire', 'Lightning', 'Thunder']

    def is_harmful(self):
        return self.has_flag('IsHarmful')

    def is_leveled(self):
        return self.has_root_spell() and self.level

    def is_member(self, spell):
        return spell in self.members

    def is_spell(self):
        return self.has_flag('IsSpell')

    def is_temporary(self):
        return self.has_flag('Temporary')

    def unset_flag(self, value):
        flags = self.flags
        if value in flags:
            flags.remove(value)
        self.data['SpellFlags'] = ';'.join(sorted(flags))

    def postfix_attribute(self, attribute, postfix, separator='_'):
        """ Postfixes an attribute such as name, taking level into consideration """
        if self.is_leveled():
            tags = getattr(self, attribute).split(separator)
            attr_tags = tags[:-1]        # base name
            attr_tags.append(postfix)    # postfix
            attr_tags.append(tags[-1])   # level
            return separator.join(attr_tags)

        return f"{getattr(self, attribute)}_{postfix}"

    def postfix_name(self, postfix, separator='_'):
        """ Creates a postfixed name """
        return self.postfix_attribute('name', postfix, separator)

    def postfix_using(self, postfix, separator='_'):
        return self.postfix_attribute('using', postfix, separator)

    def postfix_root_spell_id(self, postfix, deprioritized=False):
        return f"{self.root_spell_id}_{postfix}"

    def set_root_spell_id(self, spellname):
        if self.has_root_spell():
            self.data['RootSpellID'] = spellname

    def relink_children(self):
        """ 
            Relinks spells that inherit from properties directly from the
            root spell but otherwise are not connected to the container.

            This also regrafts children of the children into the new tree
            so there is no need to relink second or higher degree children.
        """
        relinked_spells = []
        if not self.children:
            return []
        for child in self.children:
            """ Skip spells linked to the container """
            if child.is_leveled() or self.is_member(child):
                continue

            """ Set original spell as new parent """
            parent = self.originals[child.using]
            child.using = parent.name
            child.parent = parent

            """ Register spells modified """
            relinked_spells.append(child)
        return relinked_spells

    def set_container(self, spell):
        self.data['SpellContainerID'] = spell.name

    def set_flag(self, value):
        flags = self.flags
        flags.add(value)
        self.data['SpellFlags'] = ';'.join(sorted(flags))

    def swap_element(self, to_element, from_element=None):
        if not from_element:
            from_element = self.damage_type
        self.data['DamageType'] = to_element
        for field in ('DescriptionParams', 'TooltipDamageList', 'SpellFail', 'SpellProperties', 'SpellSuccess'):
            f = self.data.get(field, None)
            if f:
                self.data[field] = f.replace(from_element, to_element)

    def to_lines(self):
        s = [
            f'new entry "{self.name}"',
            f'type "SpellData"',
            f'data "SpellType" "{self.type}"',
        ]
        if self.using:
            s.append(f'using "{self.using}"')
        for k, v in sorted(self.data.items()):
            s.append(f'data "{k}" "{v}"')
        return s

    def to_text(self):
        return '\n'.join(self.to_lines())

    def __str__(self):
        return self.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __gt__(self, other):
        return self.name > other.name

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return id(self)


class SpellLibrary:
    def __init__(self, opts):
        """ Processes spell definitions found in various text files into a single spell library """
        self.spell_map = {}     # spell_name => Spell object
        self.spell_graph = {}   # spell_name => [Children]
        self.spell_groups = {}  # spell_name => [meta Spells]
        self.opts = opts
        self.debug = opts.debug
        self.verbose = opts.verbose
        self.path = opts.path
        self.dest = opts.dest
        self.enabled = opts.enabled

        for spell_file in glob.glob(self.path, recursive=True):
            with open(spell_file, 'r') as f:
                for block in f.read().split('\n\n'):
                    if len(block) < 1:
                        continue
                    """ Parse spell defnition block into Spell object """
                    s = Spell(block=block)
                    """ Add Spell to spell map """
                    self.spell_map[s.name] = s

        """ Find containerization """
        self.link_spells()

        """ Find inheritance """
        self.build_graph()

    def link_spells(self):
        """ Links spells to their containers """
        for _, s in self.spell_map.items():
            """ Identify container of seemingly standalone spells that inherit container from parent """
            if s.has_using() and s.spell_container_id == None:
                if self.debug:
                    print(f"inhering container from parent: {s.name}")
                parent_spell = self.spell_map[s.using]
                s.copy_data(parent_spell, ['SpellContainerID'])

            """ Directly linked """
            if s.has_spell_container():
                if s.name == s.spell_container_id:
                    raise SpellLinkException(
                        f"spell {s.name} is referencing itself for containerization")
                container_spell = self.spell_map.get(
                    s.spell_container_id, None)
                if not container_spell:
                    if self.debug:
                        print(
                            f"BUG: missing container spell {s.spell_container_id} for spell {s.name}")
                    continue
                s.container = container_spell
                container_spell.members.add(s)

            """ Upleveled """
            if s.has_root_spell():
                root_spell = self.spell_map.get(s.root_spell_id, None)
                if not root_spell:
                    if self.debug:
                        print(f"root spell not seen yet for {s.name}")
                    continue
                root_spell.upleveled.add(s)

    def build_graph(self):
        """ Build inheritance using helper graph """
        for _, s in self.spell_map.items():
            """ Top level Spell, initialize """
            if s.has_no_using():
                self.spell_graph[s.name] = []
                continue

            """ Child, find and add to parent """
            parent_spell = self.spell_map.get(s.using, None)
            parent_spell.children.add(s)
            if s.name == parent_spell.name:
                raise SpellLinkException(
                    "spell is referencing itself for inheritance")
            s.parent = parent_spell

            parent_ref = self.spell_graph.get(s.using, None)
            if parent_ref:
                self.spell_graph[s.using].append(s)
            else:
                self.spell_graph[s.using] = [s]

    def create_detached_spells(self):
        spells = []
        opts = copy.copy(self.opts)
        opts.concentration = True
        opts.spell = True
        for spell in self.get_spells(opts):
            implemented_spells = []
            """ If it's not a top level spell, skip """
            if spell.parent or spell.members or spell.is_temporary():
                if self.debug:
                    print(f'skipping: {spell.name}')
                continue

            print(f"Creating variants for {spell.name}...")

            """ Save the original spells """
            # implemented_spells.extend(spell.create_originals())
            # implemented_spells.extend(spell.relink_children())

            """ Implement each level """
            for s in spell.get_upleveled_chain():
                member_spells = []
                print(f'...{s.name}')

                """ Inherit spell properties from top, if not explicitly set """
                s.inherit(spell, 'SpellFlags')

                """ Create common variant spell: behaves as the original """
                common_spell = s.create_meta(postfix='Common')
                member_spells.append(common_spell)

                """ Create detached variant spell: does not require concentration """
                detached_spell = s.create_meta(
                    postfix='Detached', deprioritized=True)
                detached_spell.unset_flag('IsConcentration')
                # detached_spell.add_cost('DetachmentCharge:1')
                detached_spell.add_cost(f'SorceryPoints:{2*s.level+1}')
                detached_spell.add_requirement_condition(
                    "HasStatus('METAMAGIC_DETACHED', context.Source)")
                member_spells.append(detached_spell)

                """ Turn the main spell into a container and link modified spells """
                s.containerize()
                s.add_members(member_spells)

                """ Decontainerize members, if inherited previously """
                for ms in member_spells:
                    ms.decontainerize()

                """ Register spells """
                implemented_spells.append(s)
                implemented_spells.extend(member_spells)

            """ Register spells to spell group also """
            self.spell_groups[spell.name] = implemented_spells
            spells.extend(implemented_spells)

            if self.debug:
                print(f"Size of spells: {len(implemented_spells)}")

        return spells

    def create_transmuted_spells(self):
        spells = []
        opts = copy.copy(self.opts)
        opts.elemental = True
        opts.spell = True
        opts.harmful = True

        for spell in self.get_spells(opts):
            implemented_spells = []
            """ If it's not a top level spell, skip """
            if spell.parent or spell.members or spell.is_temporary():
                if self.debug:
                    print(f'skipping: {spell.name}')
                continue

            print(f"Creating variants for {spell.name}...")

            """ Save the original spells """
            # implemented_spells.extend(spell.create_originals())
            # implemented_spells.extend(spell.relink_children())

            """ Implement each level """
            for s in spell.get_upleveled_chain():
                member_spells = []
                print(f'...{s.name}')

                """ Inherit spell properties from top, if not explicitly set """
                s.inherit(spell, 'SpellFlags')

                """ Create common variant spell: behaves as the original """
                common_spell = s.create_meta(postfix='Common')
                member_spells.append(common_spell)

                for element in spell.transmutable_elements:
                    transmuted_spell = s.create_meta(
                        postfix=element, deprioritized=True)
                    if not transmuted_spell.damage_type:
                        transmuted_spell.data['DamageType'] = spell.damage_type
                    transmuted_spell.swap_element(
                        to_element=element, from_element=spell.damage_type)
                    # transmuted_spell.add_cost('TransmutationCharge:1')
                    transmuted_spell.add_cost('SorceryPoint:1')
                    transmuted_spell.add_requirement_condition(
                        "HasStatus('METAMAGIC_TRANSMUTED', context.Source)")
                    member_spells.append(transmuted_spell)

                    if transmuted_spell.damage_type != element:
                        print(s.to_text())
                        print()
                        print(common_spell.to_text())
                        print()
                        print(transmuted_spell.to_text())
                        raise Exception(f"yikes, {element}")

                """ Link modified spells to container """
                s.containerize()
                s.add_members(member_spells)

                """ Decontainerize members, if inherited previously """
                for ms in member_spells:
                    ms.decontainerize()

                """ Register spells """
                implemented_spells.append(s)
                implemented_spells.extend(member_spells)

            """ Register spells to spell group also """
            self.spell_groups[spell.name] = implemented_spells
            spells.extend(implemented_spells)

            if self.debug:
                print(f"Size of spells: {len(implemented_spells)}")

        return spells

    def extend(self):
        enabled_spells = self.load_enabled_spells()
        self.create_detached_spells()
        self.create_transmuted_spells()

        for spell_group, spells in self.spell_groups.items():
            if enabled_spells.get(spell_group, None) == None:
                print(f' [-] skipping {spell_group}, not enabled')
                continue
            filename = f'{self.dest}/Spell_{spell_group}.txt'
            with open(filename, 'w') as f:
                print(f' [+] writing {spell_group}', end=' ')
                for spell in sorted(spells):
                    f.write(spell.to_text())
                    f.write('\n\n')
                print('...done!')

    def get_spells(self, opts):
        spells = []
        if opts.spellname:
            spellnames = opts.spellname
        else:
            spellnames = self.spell_map.keys()
        for sname in spellnames:
            spell = self.spell_map.get(sname, None)
            if not spell:
                continue
            if opts.spell and not spell.is_spell():
                continue
            if opts.base and not spell.has_no_container_spells():
                continue
            if opts.concentration and not spell.is_concentration():
                continue
            if opts.container and not spell.has_container_spells():
                continue
            if opts.elemental and not spell.is_elemental():
                continue
            if opts.harmful and not spell.is_harmful():
                continue
            if opts.leveled and not spell.is_leveled():
                continue
            spells.append(spell)
        return spells

    def load_enabled_spells(self):
        enabled_spells = {}
        with open(self.enabled, 'r') as f:
            for spell_name in f.read().splitlines():
                if spell_name.startswith('#'):
                    """ Comment, ignore """
                    continue
                enabled_spells[spell_name] = True
        return enabled_spells


def print_descendants(spell, attribute='children', indent=0):
    if not spell:
        return
    if indent == 0:
        print("{}{}".format(indent * " ", spell))
    else:
        print("{}{}".format(indent * " ", spell))
    l = getattr(spell, attribute)
    for child in sorted(l):
        l = getattr(child, attribute)
        print_descendants(child, attribute, indent+2)


def print_spells(opts):
    sl = SpellLibrary(opts)
    for spell in sl.get_spells(opts):
        if opts.descendants and spell.children:
            print_descendants(spell, 'children')
            continue
        if opts.members and spell.members:
            print_descendants(spell, 'members')
            continue
        print(spell.name)
        if opts.verbose:
            print("-" * 80)
            print(spell.to_text())
            print("-" * 80)
            print("Container: {}".format(spell.container))
            print("Root:      {}".format(spell.root_spell_id))
            print("Members:   {}".format(spell.joined_members))
            print("Upleveled: {}".format(spell.joined_upleveled))
            print("Parent:    {}".format(str(spell.parent)))
            print("Children:  {}".format(spell.joined_children))
            print()


if __name__ == "__main__":
    default_path = 'orig/**/*.txt'
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest='command')

    """ Displays different type of spells and their details """
    spell_cmd = subparser.add_parser('spell', help='displays spell details')
    spell_cmd.add_argument(
        'spellname', help='name of the spell to filter on', nargs='*')
    spell_cmd.add_argument(
        '-b', '--base', help='base spells only', action='store_true')
    spell_cmd.add_argument('-c', '--container',
                           help='container spells only', action='store_true')
    spell_cmd.add_argument(
        '-d', '--descendants', help='show descendants of spells', action='store_true')
    spell_cmd.add_argument('-e', '--elemental',
                           help='elemental spells only', action='store_true')
    spell_cmd.add_argument(
        '-f', '--harmful', help='harmful spells only', action='store_true')
    spell_cmd.add_argument(
        '-l', '--leveled', help='leveled spells only', action='store_true')
    spell_cmd.add_argument(
        '-m', '--members', help='show members of container spells', action='store_true')
    spell_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    spell_cmd.add_argument(
        '-s', '--spell', help='actual spells only', action='store_true')
    spell_cmd.add_argument(
        '-x', '--concentration', help='concentration spells only', action='store_true')
    spell_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ List spells """
    list_cmd = subparser.add_parser('list', help='displays spell details')
    list_cmd.add_argument(
        'spellname', help='name of the spell to filter on', nargs='*')
    list_cmd.add_argument(
        '-b', '--base', help='base spells only', action='store_true')
    list_cmd.add_argument('-c', '--container',
                          help='container spells only', action='store_true')
    list_cmd.add_argument(
        '-d', '--descendants', help='show descendants of spells', action='store_true')
    list_cmd.add_argument('-e', '--elemental',
                          help='elemental spells only', action='store_true')
    list_cmd.add_argument(
        '-f', '--harmful', help='harmful spells only', action='store_true')
    list_cmd.add_argument(
        '-l', '--leveled', help='leveled spells only', action='store_true')
    list_cmd.add_argument(
        '-m', '--members', help='show members of container spells', action='store_true')
    list_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    list_cmd.add_argument(
        '-s', '--spell', help='actual spells only', action='store_true')
    list_cmd.add_argument(
        '-x', '--concentration', help='concentration spells only', action='store_true')
    list_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ Implement detached spell """
    detach_cmd = subparser.add_parser('detach')
    detach_cmd.add_argument(
        'spellname', help='name of the concentration spell to implement', nargs='*')
    detach_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    detach_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ List detachable spells """
    list_detachable_cmd = subparser.add_parser('list-detachable')
    list_detachable_cmd.add_argument(
        'spellname', help='name of the spell to filter on', nargs='*')
    list_detachable_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    list_detachable_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    diff_cmd = subparser.add_parser('diff')
    diff_cmd.add_argument('spellname1', help='spell to compare to')
    diff_cmd.add_argument('spellname2', help='spell to compare with')
    diff_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)

    """ Implement transmuted spells """
    transmute_cmd = subparser.add_parser('transmute')
    transmute_cmd.add_argument(
        'spellname', help='name of the elemental spell to implement', nargs='*')
    transmute_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    transmute_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ Extend spells with all meta spells """
    extend_cmd = subparser.add_parser('extend')
    extend_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    extend_cmd.add_argument(
        '-e', '--enabled', help='path to load enabled spells list', default='enabled_spells.txt')
    extend_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ List transmutable spells """
    list_transmutable_cmd = subparser.add_parser('list-transmutable')
    list_transmutable_cmd.add_argument(
        'spellname', help='name of the spell to filter on', nargs='*')
    list_transmutable_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    list_transmutable_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ List super spells that are both detachable and transmutable """
    list_super_cmd = subparser.add_parser('list-super')
    list_super_cmd.add_argument(
        'spellname', help='name of the spell to filter on', nargs='*')
    list_super_cmd.add_argument(
        '-p', '--path', help='path to load spells from', default=default_path)
    list_super_cmd.add_argument(
        '-D', '--debug', help='debug operation', action='store_true')

    """ Parse arguments, detect command """
    args = vars(parser.parse_args())
    command = args.pop('command')
    opts = SpellFilterOptions()
    for k, v in args.items():
        setattr(opts, k, v)

    if command == 'spell':
        opts.verbose = True
        print_spells(opts)
    elif command == 'list':
        opts.verbose = False
        print_spells(opts)
    elif command == 'list-super':
        opts.verbose = False
        opts.concentration = True
        opts.elemental = True
        opts.spell = True
        opts.harmful = True
        print_spells(opts)
    elif command == 'list-detachable':
        opts.verbose = False
        opts.concentration = True
        print_spells(opts)
    elif command == 'list-transmutable':
        opts.verbose = False
        opts.elemental = True
        opts.spell = True
        opts.harmful = True
        print_spells(opts)
    elif command == 'detach':
        sl = SpellLibrary(opts)
        print(
            '\n'.join([f"{s.to_text()}\n" for s in sl.create_detached_spells()]))
    elif command == 'diff':
        sl = SpellLibrary(opts)
        import difflib
        spell1 = sl.get_spells(SpellFilterOptions(
            spellname=opts.spellname1))[0]
        spell2 = sl.get_spells(SpellFilterOptions(
            spellname=opts.spellname2))[0]
        if spell1 and spell2:
            print('\n'.join(difflib.unified_diff(
                spell1.to_lines(), spell2.to_lines())))
    elif command == 'transmute':
        sl = SpellLibrary(opts)
        print(
            '\n'.join([f"{s.to_text()}\n" for s in sl.create_transmuted_spells()]))
    elif command == 'extend':
        sl = SpellLibrary(opts)
        sl.extend()
