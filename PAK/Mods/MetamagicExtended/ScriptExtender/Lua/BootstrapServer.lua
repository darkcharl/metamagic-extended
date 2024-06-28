debugMode = false

--- Converts damage type to to corresponding element if the Player has one of the METAMAGIC_TRANSMUTED_* status set
local function HandleDealDamage(e)
	local caster = e.Caster
	local damageType = e.Functor.DamageType

	if (caster ~= nil) then
		local casterUuid = caster.Uuid.EntityUuid
		if Osi.IsPlayer(casterUuid) then
			local isTransmutedToAcid = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_ACID") == 1
			local isTransmutedToCold = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_COLD") == 1
			local isTransmutedToFire = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_FIRE") == 1
			local isTransmutedToLightning = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_LIGHTNING") == 1
			local isTransmutedToPoison = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_POISON") == 1
			local isTransmutedToThunder = HasActiveStatus(casterUuid, "METAMAGIC_TRANSMUTED_THUNDER") == 1
		
			if (debugMode) then
				print('-- HandleDealDamage')
				print('caster:', casterUuid)
				print('damage type:', damageType)
				_D(e)
				print('isTransmutedToAcid:', isTransmutedToAcid)
				print('isTransmutedToCold', isTransmutedToCold)
				print('isTransmutedToFire', isTransmutedToFire)
				print('isTransmutedToLightning', isTransmutedToLightning)
				print('isTransmutedToPoison', isTransmutedToPoison)
				print('isTransmutedToThunder', isTransmutedToThunder)
			end
			
			if (isTransmutedToAcid) then
				e.Functor.DamageType = "Acid"
			elseif (isTransmutedToCold) then
				e.Functor.DamageType = "Cold"
			elseif (isTransmutedToFire) then
				e.Functor.DamageType = "Fire"
			elseif (isTransmutedToLightning) then
				e.Functor.DamageType = "Lightning"
			elseif (isTransmutedToPoison) then
				e.Functor.DamageType = "Poison"
			elseif (isTransmutedToThunder) then
				e.Functor.DamageType = "Thunder"	
			end
		end
	end
end

Ext.Events.DealDamage:Subscribe(HandleDealDamage)