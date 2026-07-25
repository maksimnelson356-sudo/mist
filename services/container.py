from services.chronicle_service import ChronicleService
from services.player_service import PlayerService
from services.profile_service import ProfileService
from services.reputation_service import ReputationService
from services.movement_service import MovementService
from services.combat_service import CombatService
from services.quest_service import QuestService
from services.inventory_service import InventoryService
from services.shop_service import ShopService
from services.equipment_service import EquipmentService
from services.pvp_service import PvPService
from services.guild_service import GuildService
from services.trade_service import TradeService
from services.achievement_service import AchievementService
from services.daily_service import DailyService
from services.crafting_service import CraftingService
from services.npc_service import NPCService
from services.npc_memory_service import NPCMemoryService
from services.npc_scheduler import NPCScheduler
from services.exploration_service import ExplorationService
from services.catalog_service import CatalogService
from services.economy_service import EconomyService
from services.admin_service import AdminService
from services.weather_system import WeatherSystem
from services.time_system import TimeSystem
from services.world_event_system import WorldEventSystem
from services.world_engine import WorldEngine
from services.ecosystem_service import EcosystemService
from services.artifact_service import ArtifactService
from services.guild_territory import GuildTerritoryService
from services.home_service import HomeService
from services.npc_life_engine import NPCLifeEngine
from services.world_memory_service import WorldMemoryService
from services.guild_war_service import GuildWarService
from services.npc_quest_service import NPCQuestService
from services.seasonal_quest_service import SeasonalQuestService
from services.seasonal_event_service import SeasonalEventService
from services.world_chronicle_service import WorldChronicleService
from services.world_boss_service import WorldBossService
from services.class_service import ClassService
from services.dialogue_service import DialogueService
from services.faction_service import FactionService
from services.raid_service import RaidService
from services.event_participation_service import EventService
from services.market_service import MarketService
from services.leaderboard_service import LeaderboardService
from services.guild_extension_service import GuildExtensionService
from services.daily_event_service import DailyEventService
from services.analytics_service import AnalyticsService
from services.daily_reward_service import DailyRewardService


class ServiceContainer:
    def __init__(self):
        self.chronicle = ChronicleService()
        self.player = PlayerService(self.chronicle)
        self.profile = ProfileService(self.chronicle, self.player)
        self.reputation = ReputationService(self.chronicle, self.player)
        self.movement = MovementService(self.chronicle, self.player)
        self.combat = CombatService(self.chronicle, self.player)
        self.quest = QuestService(self.chronicle, self.player)
        self.inventory = InventoryService(self.chronicle)
        self.shop = ShopService(self.chronicle, self.player, self.inventory)
        self.equipment = EquipmentService()
        self.pvp = PvPService(self.chronicle, self.player)
        self.guild = GuildService(self.chronicle, self.player)
        self.trade = TradeService(self.chronicle, self.player, self.inventory)
        self.achievement = AchievementService(self.chronicle, self.player)
        self.daily = DailyService(self.chronicle, self.player)
        self.crafting = CraftingService(self.chronicle, self.player, self.inventory)
        self.npc = NPCService(self.chronicle)
        self.npc_memory = NPCMemoryService(self.chronicle)
        self.exploration = ExplorationService(self.chronicle, self.player)
        self.catalog = CatalogService(self.chronicle)
        self.economy = EconomyService(self.chronicle, self.player)
        self.admin = AdminService(self.chronicle, self.player)
        self.weather = WeatherSystem(self.chronicle)
        self.time = TimeSystem(self.chronicle)
        self.world_events = WorldEventSystem(self.chronicle)

        self.ecosystem = EcosystemService(self.chronicle)
        self.artifact = ArtifactService(self.chronicle)
        self.guild_territory = GuildTerritoryService(self.chronicle)
        self.home = HomeService(self.chronicle)
        self.npc_life = NPCLifeEngine(self.chronicle)
        self.world_memory = WorldMemoryService(self.chronicle)
        self.guild_war = GuildWarService(self.chronicle)
        self.npc_quest = NPCQuestService(self.chronicle)
        self.seasonal_quest = SeasonalQuestService(self.chronicle)
        self.seasonal_event = SeasonalEventService(self.chronicle)
        self.world_chronicle = WorldChronicleService(self.chronicle)
        self.world_boss = WorldBossService(self.chronicle)
        self.player_class = ClassService(self.chronicle, self.player)
        self.dialogue = DialogueService(self.chronicle, self.player)
        self.faction = FactionService(self.chronicle, self.player)
        self.raid = RaidService(self.chronicle, self.player)
        self.event = EventService(self.chronicle, self.player)
        self.market = MarketService(self.chronicle)
        self.leaderboard = LeaderboardService(self.chronicle)
        self.guild_ext = GuildExtensionService(self.chronicle, self.player)
        self.daily_event = DailyEventService(self.chronicle)
        self.analytics = AnalyticsService(self.chronicle)
        self.daily_reward = DailyRewardService(self.chronicle, self.player, self.inventory)

        self.npc_scheduler = NPCScheduler(self.npc)

        self.world_engine = WorldEngine(
            self.chronicle,
            ecosystem=self.ecosystem,
            guild_territory=self.guild_territory,
            home_service=self.home,
            npc_life=self.npc_life,
            world_memory=self.world_memory,
            seasonal_quest=self.seasonal_quest,
            world_boss=self.world_boss,
            seasonal_event=self.seasonal_event,
            daily_event=self.daily_event,
            npc_scheduler=self.npc_scheduler,
        )

        self.user = self.player


services = ServiceContainer()
