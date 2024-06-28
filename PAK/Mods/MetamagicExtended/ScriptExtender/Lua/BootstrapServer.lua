Debug = false

local function TransmuteDamage(e, damage_type)
	local originalDamageType = e.Hit.DamageType
	local originalDamageDone = e.Hit.TotalDamageDone

	if (Debug) then
		_P('-- originalDamageType')
		_D(originalDamageType)
		_P('-- originalDamageDone')
		_D(originalDamageDone)
	end

	e.Hit.DamageType = damage_type
	e.Hit.DeathType = damage_type

	if (e.Hit.Results.ConditionRoll.DamageTypeParams[1] ~= nil) then
		e.Hit.Results.ConditionRoll.DamageTypeParams[1] = damage_type
	end

	if (e.Hit.Results.DamageRolls) then
		local damageRollForOriginalType = e.Hit.Results.DamageRolls[originalDamageType]
		e.Hit.Results.DamageRolls[damage_type] = damageRollForOriginalType
	end
end

--- Converts damage type to to corresponding element if the Player has one of the METAMAGIC_TRANSMUTED_* status set
---@param e EsvLuaBeforeDealDamageEvent
local function HandleBeforeDealDamage(e)
	if (e.Hit ~= nil and e.Hit.Inflicter ~= nil and e.Hit.Results ~= nil) then
		local inflicterEntityUuid = e.Hit.Inflicter.Uuid.EntityUuid
		local isTransmutedToAcid = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_ACID") == 1
		local isTransmutedToCold = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_COLD") == 1
		local isTransmutedToFire = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_FIRE") == 1
		local isTransmutedToLightning = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_LIGHTNING") == 1
		local isTransmutedToPoison = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_POISON") == 1
		local isTransmutedToThunder = HasActiveStatus(inflicterEntityUuid, "METAMAGIC_TRANSMUTED_THUNDER") == 1

		if (Debug) then
			_P('-- isTransmutedToAcid')
			_D(isTransmutedToAcid)
			_P('-- isTransmutedToCold')
			_D(isTransmutedToCold)
			_P('-- isTransmutedToFire')
			_D(isTransmutedToFire)
			_P('-- isTransmutedToLightning')
			_D(isTransmutedToLightning)
			_P('-- isTransmutedToPoison')
			_D(isTransmutedToPoison)
			_P('-- isTransmutedToThunder')
			_D(isTransmutedToThunder)
		end
		
		if (Osi.IsPlayer(inflicterEntityUuid)) then
			if (isTransmutedToAcid) then
				TransmuteDamage(e, "Acid")
			elseif (isTransmutedToCold) then
				TransmuteDamage(e, "Cold")
			elseif (isTransmutedToFire) then
				TransmuteDamage(e, "Fire")
			elseif (isTransmutedToLightning) then
				TransmuteDamage(e, "Lightning")
			elseif (isTransmutedToPoison) then
				TransmuteDamage(e, "Poison")
			elseif (isTransmutedToThunder) then
				TransmuteDamage(e, "Thunder")	
			end
		end
	end
end

Ext.Events.BeforeDealDamage:Subscribe(HandleBeforeDealDamage)