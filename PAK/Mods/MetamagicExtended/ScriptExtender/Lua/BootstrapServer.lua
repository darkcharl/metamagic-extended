debugMode = true

TransmutedSpells = {}

local function has_spell_flag(t)
	for _, flag in ipairs(t) do
		if flag == 'IsSpell' then
			return true
		end
	end

	return false
end

local function has_spell(t, spellName)
    for sName, dType in pairs(t) do
        if sName == spellName then
            return true
        end
    end

    return false
end

local function SetDamageType(e, damageType)
	originalDamageType = e.Functor.DamageType
	e.Functor.DamageType = damageType

	if (debugMode) then
		print('--- SetDamageType')
		print('original damage type:', originalDamageType)
		print('set damage type:', damageType)
	end

	if not(has_spell(TransmutedSpells, e.SpellId.Prototype)) then
		TransmutedSpells[e.SpellId.Prototype] = originalDamageType
	end
end

--- Converts damage type to to corresponding element if the Player has one of the METAMAGIC_TRANSMUTED_* status set
local function HandleDealDamage(e)
	local caster = e.Caster
	local damageType = e.Functor.DamageType
	local spellName = e.SpellId.Prototype

	if (caster ~= nil and damageType ~= "None") then
		local casterUuid = caster.Uuid.EntityUuid
		local spellFlags = e.SpellId.SpellProto.SpellFlags
		if Osi.IsPlayer(casterUuid) and has_spell_flag(spellFlags) then
			local isTransmutedToAcid = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_ACID") == 1
			local isTransmutedToCold = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_COLD") == 1
			local isTransmutedToFire = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_FIRE") == 1
			local isTransmutedToLightning = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_LIGHTNING") == 1
			local isTransmutedToPoison = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_POISON") == 1
			local isTransmutedToThunder = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_THUNDER") == 1
		
			if (debugMode) then
				print('-- HandleDealDamage')
				print('caster:', casterUuid)
				print('spell name:', spellName)
				print('damage type:', damageType)
				print('spell flags:')
				_D(spellFlags)
				print('has spell flag:', has_spell_flag(spellFlags))
				-- _D(e)
				print('isTransmutedToAcid:', isTransmutedToAcid)
				print('isTransmutedToCold', isTransmutedToCold)
				print('isTransmutedToFire', isTransmutedToFire)
				print('isTransmutedToLightning', isTransmutedToLightning)
				print('isTransmutedToPoison', isTransmutedToPoison)
				print('isTransmutedToThunder', isTransmutedToThunder)
			end
			
			if (isTransmutedToAcid) then
				SetDamageType(e, "Acid")
			elseif (isTransmutedToCold) then
				SetDamageType(e, "Cold")
			elseif (isTransmutedToFire) then
				SetDamageType(e, "Fire")
			elseif (isTransmutedToLightning) then
				SetDamageType(e, "Lightning")
			elseif (isTransmutedToPoison) then
				SetDamageType(e, "Poison")
			elseif (isTransmutedToThunder) then
				SetDamageType(e, "Thunder")
			elseif has_spell(TransmutedSpells, spellName) then
				if (debugMode) then
					print('resetting damage back')
					print('original damage:', TransmutedSpells[spellName])
				end
				e.Functor.DamageType = TransmutedSpells[spellName]
				TransmutedSpells[spellName] = nil
			end

			if (debugMode) then
				print('List of transmuted spells:')
				_D(TransmutedSpells)
			end
		end
	end
end

Ext.Events.DealDamage:Subscribe(HandleDealDamage)