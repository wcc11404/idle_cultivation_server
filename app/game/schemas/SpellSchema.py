from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class EquipSpellRequest(BaseRequest):
    spell_id: str


class UnequipSpellRequest(BaseRequest):
    spell_id: str


class UpgradeSpellRequest(BaseRequest):
    spell_id: str


class ChargeSpellRequest(BaseRequest):
    spell_id: str
    amount: int


class SpellListResponse(BaseResponse):
    player_spells: dict
    equipped_spells: dict
    spells_config: dict
