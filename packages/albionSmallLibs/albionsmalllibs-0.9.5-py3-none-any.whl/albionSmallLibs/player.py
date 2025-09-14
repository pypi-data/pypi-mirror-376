from enum import Enum

HEAL_WEAPON =  ['NATURESTAFF', 'HOLYSTAFF', 'DIVINESTAFF', 'WILDSTAFF']
DPS_WEAPON = ['HALBERD', 'AXE', 'KNUCKLES', 'SWORD', 'CROSSBOW', 'DAGGER',
              'SPEAR', 'BOW' , 'GLACIALSTAFF', 'SCYTHE', 'INFERNOSTAFF',
              'FIRE', 'CLAYMORE','SCIMITAR', 'GLAIVE', 'HARPOON', 'RAPIER',
              'FROSTSTAFF','ICECRYSTAL', 'CLAWPAIR', 'DUALSICKLE', 'CLEAVER',
              'SHAPESHIFTER_SET1',  'SHAPESHIFTER_SET3', 'SHAPESHIFTER_AVALON', 
              'SHAPESHIFTER_HELL' ]
TANK_WEAPON = ['HAMMER', 'MACE', 'FLAIL', 'IRONCLADEDSTAFF', 'ROCKSTAFF', 'TRIDENT',
               'RAM', 'SHAPESHIFTER_KEEPER']
SUPPORT_WEAPON = ['COMBATSTAFF', 'ARCANE', 'CURSEDSTAFF', 'ENIGMATICSTAFF',
                  'DEMONICSTAFF', 'ENIGMATICORB','ICEGAUNTLETS',
                  'DOUBLEBLADEDSTAFF', 'QUARTERSTAFF', 'SHAPESHIFTER_SET2']


BATTLE_MOUNTS = {"T8_MOUNT_MAMMOTH_BATTLE@1","T7_MOUNT_SWAMPDRAGON_BATTLE","T7_MOUNT_ARMORED_SWAMPDRAGON_BATTLE","T6_MOUNT_SIEGE_BALLISTA",
"T6_MOUNT_SIEGE_BALLISTA","UNIQUE_MOUNT_RHINO_SEASON_CRYSTAL","UNIQUE_MOUNT_RHINO_SEASON_GOLD","UNIQUE_MOUNT_RHINO_SEASON_SILVER","UNIQUE_MOUNT_RHINO_SEASON_BRONZE",
"UNIQUE_MOUNT_TOWER_CHARIOT_CRYSTAL","UNIQUE_MOUNT_TOWER_CHARIOT_GOLD","UNIQUE_MOUNT_TOWER_CHARIOT_SILVER","UNIQUE_MOUNT_ARMORED_EAGLE_CRYSTAL","UNIQUE_MOUNT_ARMORED_EAGLE_GOLD",
"UNIQUE_MOUNT_ARMORED_EAGLE_SILVER","UNIQUE_MOUNT_BEETLE_CRYSTAL","UNIQUE_MOUNT_BEETLE_GOLD","UNIQUE_MOUNT_BEETLE_SILVER","UNIQUE_MOUNT_BEHEMOTH_CRYSTAL","UNIQUE_MOUNT_BEHEMOTH_GOLD",
"UNIQUE_MOUNT_BEHEMOTH_SILVER","UNIQUE_MOUNT_ENT_CRYSTAL","UNIQUE_MOUNT_ENT_GOLD","UNIQUE_MOUNT_ENT_SILVER","UNIQUE_MOUNT_BATTLESPIDER_CRYSTAL",
"UNIQUE_MOUNT_BATTLESPIDER_GOLD","UNIQUE_MOUNT_BATTLESPIDER_SILVER","UNIQUE_MOUNT_BASTION_CRYSTAL","UNIQUE_MOUNT_BASTION_GOLD","UNIQUE_MOUNT_BASTION_SILVER",
"UNIQUE_MOUNT_JUGGERNAUT_CRYSTAL","UNIQUE_MOUNT_JUGGERNAUT_GOLD","UNIQUE_MOUNT_JUGGERNAUT_SILVER","UNIQUE_MOUNT_TANKBEETLE_CRYSTAL","UNIQUE_MOUNT_TANKBEETLE_GOLD",
"UNIQUE_MOUNT_TANKBEETLE_SILVER"}

class Role(Enum):
    HEAL = 1
    DPS = 2
    TANK = 3
    SUPPORT = 4
    BATTLE_MOUNTS = 5
    OTHER = 6

class Player:
    def __init__(self, name: str, weapon: dict, ip : float, guildName = None, allianceName = None):
        self.name = name
        self.ip = ip
        self.guild = guildName
        self.alliance = allianceName
        if weapon is None:
            self.weaponFullName = "None"
        else:
            self.weaponFullName = weapon['Type']
    
    
    def getType(self):
        weapon_name = self.getWeaponKeyWord()
        if(weapon_name== "BATTLE_MOUNTS"):
            return Role.BATTLE_MOUNTS
        elif any(weapon in weapon_name for weapon in HEAL_WEAPON):
            return Role.HEAL
        elif any(weapon in weapon_name for weapon in TANK_WEAPON):
            return Role.TANK
        elif any(weapon in weapon_name for weapon in DPS_WEAPON):
            return Role.DPS
        elif any(weapon in weapon_name for weapon in SUPPORT_WEAPON):
            return Role.SUPPORT
        else:
            return Role.OTHER

    def getWeaponKeyWord(self):
        if(self.weaponFullName == "BATTLE_MOUNTS"):
            return self.weaponFullName
        splitStr = self.weaponFullName.split("_")
        if len(splitStr)>=3:
            weapon = splitStr[2].split('@')[0]
            if weapon == "SHAPESHIFTER":
                return "SHAPESHIFTER_"+ splitStr[3].split('@')[0]
            return weapon
        else:
            return self.weaponFullName

    def getWeaponName(self):
        if(self.weaponFullName == "BATTLE_MOUNTS"):
            return self.weaponFullName
        splitStr = self.weaponFullName.split("_")
        if len(splitStr)>=3:
            weapon = splitStr[2].split('@')[0]
            if weapon == "SHAPESHIFTER":
                return "SHAPESHIFTER_"+ splitStr[3].split('@')[0]
            return '_'.join(splitStr[2:]).split("@")[0]
        else:
            return self.weaponFullName

    def __str__(self):
        return f"player {self.name} from {self.guild} playing {self.weaponFullName} ({self.getType().name}) at {self.ip} ip"