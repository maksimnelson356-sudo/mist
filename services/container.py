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
from services.quest_engine import QuestEngine


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
        self.npc_scheduler = NPCScheduler(self.npc)
        self.exploration = ExplorationService(self.chronicle, self.player)
        self.catalog = CatalogService(self.chronicle)
        self.economy = EconomyService(self.chronicle, self.player)
        self.admin = AdminService(self.chronicle, self.player)
        self.weather = WeatherSystem(self.chronicle)
        self.time = TimeSystem(self.chronicle)
        self.world_events = WorldEventSystem(self.chronicle)
        self.quest_engine = QuestEngine(self.chronicle)

        self.user = self.player  # backward compat


services = ServiceContainer()
